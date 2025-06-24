import pygame
import numpy as np
from tsp import TSP

# Pygameの初期設定
pygame.init()

class Config:
    """ 設定値をまとめるクラス """
    DEFAULT_WIDTH = 800  # 初期画面幅
    DEFAULT_HEIGHT = 600  # 初期画面高さ
    UI_HEIGHT = 60  # UIエリアの高さ
    DSP_HEIGHT = 60  # DSPエリアの高さ

    BG_COLOR = (30, 30, 30)
    CITY_COLOR = (0, 150, 255)
    LINE_COLOR = (255, 255, 255)
    TEXT_COLOR = (255, 255, 255)
    BUTTON_COLOR = (70, 70, 70)
    BUTTON_HOVER_COLOR = (100, 100, 100)
    INPUT_BOX_COLOR = (200, 200, 200)

    CITY_RADIUS_RATIO = 0.05 # 画面横サイズに対する都市サイズの割合
    MINIMUM_CITY_RADIUS = 8  # 都市円の描画サイズの下限
    COORD_MIN, COORD_MAX = 0, 100  # 都市座標のスケール範囲

    BUTTON_WIDTH = 120
    BUTTON_HEIGHT = 40
    BUTTON_GAP = 30

    FONT_SIZE = 24  # フォントサイズ
    MARGIN_RATIO = 0.05  # 画面の5%を余白として確保

    FPS = 60 # フレームレート

class TSP_GUI:
    BUTTONS = ["Reset(R)", "Undo(Z)", "Settings(S)", "Quit(Q)"]
    SETTING_BUTTONS = ["Apply(A)", "Return(R)"]

    # 画面の状態を管理
    MAIN_SCREEN = "main"
    SETTINGS_SCREEN = "settings"

    def __init__(self):
        pygame.display.set_caption("TSP - Route Selection")

        self.screen = pygame.display.set_mode((Config.DEFAULT_WIDTH, Config.DEFAULT_HEIGHT + Config.UI_HEIGHT + Config.DSP_HEIGHT), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        
        self.current_screen = self.MAIN_SCREEN  # 初期状態はメイン画面

        self.route = []  # 選択されたルート
        self.running = True
        self.show_settings = False  # 設定画面の表示フラグ

        # フォント設定
        self.font = pygame.font.Font(None, Config.FONT_SIZE)

        # ボタンの定義（動的に配置）
        self.buttons, self.settings_buttons = self.create_buttons()

        # 設定用の入力フィールド
        rng = np.random.default_rng(42)
        self.tsp = TSP(num_cities=10, coord_min=Config.COORD_MIN, coord_max=Config.COORD_MAX, rng=rng)
        self.input_boxes = {
            "都市数": pygame.Rect(300, 200, 140, 32),
            "Seed": pygame.Rect(300, 250, 140, 32)
        }
        self.active_input = None
        
        # 都市表示円の大きさ
        self.city_radius = Config.MINIMUM_CITY_RADIUS

    def create_buttons(self):
        """ ボタンの配置を動的に決定 """
        width, height = self.screen.get_size()
        y_pos = height - Config.UI_HEIGHT + (Config.UI_HEIGHT - Config.BUTTON_HEIGHT) // 2
        
        def calculate_x_start(num_buttons):
            return (width - (Config.BUTTON_WIDTH * num_buttons + Config.BUTTON_GAP * 2)) // 2

        x_start = calculate_x_start(len(self.BUTTONS))
        buttons = {}
        for i, button_name in enumerate(self.BUTTONS):
            buttons[button_name] = pygame.Rect(x_start + (Config.BUTTON_WIDTH + Config.BUTTON_GAP) * i, y_pos, Config.BUTTON_WIDTH, Config.BUTTON_HEIGHT)

        x_start = calculate_x_start(len(self.SETTING_BUTTONS))
        settings_buttons = {}
        for i, button_name in enumerate(self.SETTING_BUTTONS):
            settings_buttons[button_name] = pygame.Rect(x_start + (Config.BUTTON_WIDTH + Config.BUTTON_GAP) * i, y_pos, Config.BUTTON_WIDTH, Config.BUTTON_HEIGHT)

        return buttons, settings_buttons

    def run(self):
        """ メインループ """
        while self.running:
            self.screen.fill(Config.BG_COLOR)
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(Config.FPS)

    def handle_events(self):
        """ イベント処理 """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:  # ウィンドウサイズ変更
                # ウィンドウサイズを再設定
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self.buttons, self.settings_buttons = self.create_buttons()
                width, height = self.screen.get_size()
                city_radius = min(width, height)*Config.CITY_RADIUS_RATIO
                self.city_radius = min(city_radius, Config.MINIMUM_CITY_RADIUS)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.current_screen == self.MAIN_SCREEN:
                    self.handle_click_main(event.pos)
                elif self.current_screen == self.SETTINGS_SCREEN:
                    self.handle_click_setting(event.pos)
            elif event.type == pygame.KEYDOWN:
                if self.current_screen == self.MAIN_SCREEN:
                    self.handle_key_main(event)
                elif self.current_screen == self.SETTINGS_SCREEN:
                    self.handle_key_setting(event)

    def handle_click_main(self, pos):
        """ クリック処理（都市 or ボタン） """
        for button_name, rect in self.buttons.items():
            if rect.collidepoint(pos):
                if button_name == "Reset(R)":
                    self.reset_route()
                elif button_name == "Undo(Z)":
                    self.undo_last_selection()
                elif button_name == "Settings(S)":
                    self.current_screen = self.SETTINGS_SCREEN  # 設定画面へ移行
                elif button_name == "Quit(Q)":
                    self.running = False
                return  

        # 都市の選択処理
        for i, city in enumerate(self.tsp.cities):
            screen_x, screen_y = self.coord_to_screen(city)

            if np.linalg.norm(np.array(pos) - np.array([screen_x, screen_y])) < self.city_radius*1.2:
                if i not in self.route:
                    self.route.append(i)
    
    def handle_click_setting(self, pos):
        for key, rect in self.input_boxes.items():
                if rect.collidepoint(pos):
                    self.active_input = key
                    return
        for button_name, rect in self.settings_buttons.items():
            if rect.collidepoint(pos):
                if button_name == "Apply(A)":
                    self.apply_settings()  # 設定適用
                if button_name == "Return(R)":
                    self.current_screen = self.MAIN_SCREEN  # 設定画面から戻る

    def handle_key_main(self, event):
        if event.key == pygame.K_r:  
            self.reset_route()  # ルートをリセット
        if event.key == pygame.K_q:  
            self.running = False  # 終了
        if event.key == pygame.K_z:  
            self.undo_last_selection()  # 設定したルートをひとつ戻す
        if event.key == pygame.K_s:
            self.current_screen = self.SETTINGS_SCREEN  # 設定画面に移行

    def handle_key_setting(self, event):
        if event.key == pygame.K_a :
            self.apply_settings()  # 設定適用
        if event.key == pygame.K_r:
            self.current_screen = self.SETTINGS_SCREEN  # メイン画面に移行

    def reset_route(self):
        """ ルートをリセット """
        self.route = []

    def undo_last_selection(self):
        """ 最後の選択を元に戻す """
        if self.route:
            self.route.pop()

    def coord_to_screen(self, coord):
        """ 座標を画面スケールに変換 """
        x, y = coord
        width, height = self.screen.get_size()
        margin_x = width * Config.MARGIN_RATIO
        margin_y = height * Config.MARGIN_RATIO
        
        screen_x = int(margin_x + (x - Config.COORD_MIN) / (Config.COORD_MAX - Config.COORD_MIN) * (width - 2 * margin_x))
        screen_y = int(margin_y + (y - Config.COORD_MIN) / (Config.COORD_MAX - Config.COORD_MIN) * (height - 2 * margin_y))
        
        return screen_x, screen_y

    def screen_to_coord(self, pos):
        """ 画面座標を元の座標スケールに変換 """
        x, y = pos
        width, height = self.screen.get_size()
        margin_x = width * Config.MARGIN_RATIO
        margin_y = height * Config.MARGIN_RATIO

        coord_x = Config.COORD_MIN + (x - margin_x) / (width - 2 * margin_x) * (Config.COORD_MAX - Config.COORD_MIN)
        coord_y = Config.COORD_MIN + (y - margin_y) / (height - 2 * margin_y) * (Config.COORD_MAX - Config.COORD_MIN)

        return int(coord_x), int(coord_y)

    def draw(self):
        """ 画面の描画 """
        if self.current_screen == self.MAIN_SCREEN:
            self.draw_main_screen()
        elif self.current_screen == self.SETTINGS_SCREEN:
            self.draw_settings_screen()

    def draw_main_screen(self):
        """ メイン画面の描画 """
        for i, city in enumerate(self.tsp.cities):
    screen_x, screen_y = self.coord_to_screen(city)
    
    # クリックされた都市だけ緑色で表示
    city_color = (0, 255, 0) if i in self.route else Config.CITY_COLOR
    pygame.draw.circle(self.screen, city_color, (screen_x, screen_y), self.city_radius)

    text_surface = self.font.render(str(i), True, Config.TEXT_COLOR)
    self.screen.blit(text_surface, (screen_x + 12, screen_y - 12))

        # ルートの描画
        if len(self.route) > 1:
            for i in range(len(self.route) - 1):
                city1 = self.coord_to_screen(self.tsp.cities[self.route[i]])
                city2 = self.coord_to_screen(self.tsp.cities[self.route[i + 1]])
                pygame.draw.line(self.screen, Config.LINE_COLOR, city1, city2, 2)

            # 最後の都市から最初の都市へ閉じる（巡回ルート）
            if len(self.route) == self.tsp.num_cities:
                pygame.draw.line(self.screen, Config.LINE_COLOR, self.coord_to_screen(self.tsp.cities[self.route[-1]]), self.coord_to_screen(self.tsp.cities[self.route[0]]), 2)
        
        # ルート情報の表示
        width, height = self.screen.get_size()
        info_text = "Route: " + " -> ".join(map(str, self.route))
        text_surface = self.font.render(info_text, True, Config.TEXT_COLOR)
        # y_pos = height - (Config.UI_HEIGHT + Config.DSP_HEIGHT) + (Config.DSP_HEIGHT - Config.FONT_SIZE) // 2
        y_pos = height - (Config.UI_HEIGHT + Config.DSP_HEIGHT)
        self.screen.blit(text_surface, (10, y_pos))

        # ボタンの描画
        for name, rect in self.buttons.items():
            mouse_pos = pygame.mouse.get_pos()
            color = Config.BUTTON_HOVER_COLOR if rect.collidepoint(mouse_pos) else Config.BUTTON_COLOR
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            text_surface = self.font.render(name, True, Config.TEXT_COLOR)
            self.screen.blit(text_surface, text_surface.get_rect(center=rect.center))

    def draw_settings_screen(self):
        """ 設定画面の描画 """
        self.screen.fill((50, 50, 50))  # 背景色変更
        text_surface = self.font.render("Settings Screen", True, Config.TEXT_COLOR)
        self.screen.blit(text_surface, (Config.DEFAULT_WIDTH // 2 - 100, Config.DEFAULT_HEIGHT // 2 - 50))

        # ボタンの描画
        for name, rect in self.settings_buttons.items():
            mouse_pos = pygame.mouse.get_pos()
            color = Config.BUTTON_HOVER_COLOR if rect.collidepoint(mouse_pos) else Config.BUTTON_COLOR
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            text_surface = self.font.render(name, True, Config.TEXT_COLOR)
            self.screen.blit(text_surface, text_surface.get_rect(center=rect.center))
        
        # 入力ボックスの表示
        for label, rect in self.input_boxes.items():
            pygame.draw.rect(self.screen, Config.INPUT_BOX_COLOR, rect, border_radius=5)
            pygame.draw.rect(self.screen, Config.TEXT_COLOR, rect, 2, border_radius=5)
            text_surface = self.font.render(label + ": " + (self.num_cities if label == "Cities" else self.seed), True, Config.INPUT_TEXT_COLOR)
            self.screen.blit(text_surface, (rect.x + 5, rect.y + 5))

if __name__ == "__main__":
    gui = TSP_GUI()
    gui.run()

    pygame.quit()
