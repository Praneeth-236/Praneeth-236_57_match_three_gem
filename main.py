import sys
import pygame
from game.game_engine import GameEngine

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 650
FPS = 60


def main():
    pygame.init()
    pygame.display.set_caption("Match-3 Gem Swap")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    engine = GameEngine(SCREEN_WIDTH, SCREEN_HEIGHT)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                engine.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                engine.reset()

        dt = clock.tick(FPS) / 1000.0
        engine.update(dt)
        engine.render(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()