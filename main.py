import pygame
import sys
import threading
import time
import random
from config import *
from graphics_fx import *
from arduino_input_handler import Joystick
from game_objects import Character, BulletManager, Money


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        pygame.display.set_caption('Scrolling Chessboard with Joystick Control')

        # Initialize game objects
        self.character = Character()
        self.bullet_manager = BulletManager()
        self.money = Money()

        self.offset_y = 0
        self.score = 0

        # Initialize joystick handler
        self.joystick = Joystick()
        self.joystick.start_reading()

        # Game state flag
        self.game_over = False
        self.play_again = False

        # Collection message
        self.collection_message = ""
        self.message_visible = False
        self.message_disappear_time = None
        self.message_duration = 1.0  # Duration the message stays visible in seconds

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Loop background music
            if not background_channel.get_busy():
                background_channel.play(background_music)

            # Update game state
            self.update()

            # Draw everything
            self.render()

            pygame.display.flip()
            pygame.time.delay(30)

        pygame.quit()
        sys.exit()

    def update(self):
        # Update scrolling background
        self.offset_y += SCROLL_SPEED
        if self.offset_y >= TILE_HEIGHT:
            self.offset_y = 0

        # Update character position
        velocity_x, velocity_y = self.joystick.get_velocity()
        self.character.move(velocity_x, velocity_y)

        # Update bullets
        self.bullet_manager.update()

        # Check for collisions with money
        if self.money.visible and self.character.check_collision(self.money.x, self.money.y):
            points = self.money.collect()
            self.score += points
            self.collection_message = f"+${points}!"
            self.message_visible = True
            self.message_disappear_time = pygame.time.get_ticks()

        elif not self.money.visible:
            self.money.respawn()

        if self.character.check_bullet_collision(self.bullet_manager.bullets):
            self.character.health -= BULLET_DAMAGE
            # Play the gunshot sound only if it's not already playing
            if not gunshot_channel.get_busy():
                gunshot_channel.play(gunshot_sound)

        if self.character.health <= 0:
            self.game_over = True
            self.play_again = True
            return

    def render(self):
        # Clear screen
        self.screen.fill((0, 0, 0))

        # Draw scrolling background
        draw_tiled_background(self.screen, self.offset_y)

        if self.game_over:
            self.show_end_screen()

        else:
            # Draw character
            self.character.draw(self.screen)

            # Draw bullets
            self.bullet_manager.draw(self.screen)

            # Draw money
            self.money.draw(self.screen)

            # Draw score
            draw_bank(self.screen, BANK_X, BANK_Y)
            draw_score(self.screen, self.score, BANK_X, BANK_Y)

            # Draw health bar
            self.draw_health_bar()

            if self.message_visible:
                self.draw_collection_message()
                if pygame.time.get_ticks() - self.message_disappear_time > self.message_duration * 1000:
                    self.message_visible = False

    def show_end_screen(self):
        # Stop the gunshot sound
        gunshot_channel.stop()

        # Calculate the center of the screen
        end_image_x = (WINDOW_SIZE - end_image.get_width()) // 2
        end_image_y = (WINDOW_SIZE - end_image.get_height()) // 2

        # Draw the end image in the center
        self.screen.blit(end_image, (end_image_x, end_image_y))

        # Draw the score text underneath the end image
        font = pygame.font.Font(None, 96)  # Use a larger font size for the score
        score_text = font.render(f"Your score was {self.score}.", True, BLOOD_RED)
        text_x = (WINDOW_SIZE - score_text.get_width()) // 2
        text_y = end_image_y + end_image.get_height()  # Position below the image
        self.screen.blit(score_text, (text_x, text_y))

        score_text = font.render(f"Click to play again!", True, BLOOD_RED)
        self.screen.blit(score_text, (text_x, text_y + 60))

        if self.joystick.joystick_switch == 0:
            self.reset_game()
            return

    def reset_game(self):
        # Reset character's position and health
        self.character.reset_position()  # You need to implement this method in your character class
        self.character.health = START_HEALTH  # Set to whatever the initial health is

        # Reset the score
        self.score = 0

        # Reset the bullet manager
        self.bullet_manager.reset()  # Implement this method in your bullet manager class

        # Reset the money
        self.money.respawn()  # Or whatever the initial state should be

        # Reset any other necessary game state
        self.game_over = False
        self.play_again = False

        # Reset other game-related states like enemies, obstacles, etc.
        # self.enemies.reset()  # If you have enemies, implement this method in your enemies manager

    def draw_health_bar(self):
        # Define the size and position of the health bar
        bar_width = BANK_SIZE
        bar_height = 20
        bar_x = 50  # Mirrored to where the bank is (adjust as needed)
        bar_y = 100

        # Calculate the width of the health bar
        health_percentage = max(self.character.health / START_HEALTH, 0)
        green_width = int(bar_width * health_percentage)
        red_width = bar_width - green_width

        # Draw the green portion of the health bar
        pygame.draw.rect(self.screen, (0, 255, 0), (bar_x, bar_y, green_width, bar_height))

        # Draw the red portion of the health bar (if any)
        if red_width > 0:
            pygame.draw.rect(self.screen, (255, 0, 0), (bar_x + green_width, bar_y, red_width, bar_height))

        # Position the heart image at the right edge of the green bar
        heart_x = bar_x + green_width - heart_image.get_width() // 2  # Position at the end of the green bar
        heart_y = bar_y + (bar_height - heart_image.get_height()) // 2  # Centered vertically with the bar
        self.screen.blit(heart_image, (heart_x, heart_y))

    def draw_collection_message(self):
        font = pygame.font.Font(None, 36)  # Use the default font, size 36
        message_text = font.render(self.collection_message, True, MONEY_GREEN)
        self.screen.blit(message_text, (self.money.x, self.money.y - 40))  # Display above the money


if __name__ == "__main__":
    game = Game()
    game.run()
