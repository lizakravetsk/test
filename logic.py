"""
Модуль игровой логики для игры про шарики.
Отвечает за движение, взаимодействие и управление шариками.
"""

import math
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class Color:
    """Класс для представления цвета в RGB."""
    
    def __init__(self, r: int, g: int, b: int):
        self.r = max(0, min(255, r))
        self.g = max(0, min(255, g))
        self.b = max(0, min(255, b))
    
    def to_tuple(self) -> Tuple[int, int, int]:
        """Возвращает цвет как кортеж (r, g, b)."""
        return (self.r, self.g, self.b)
    
    def __repr__(self):
        return f"Color({self.r}, {self.g}, {self.b})"


@dataclass
class Ball:
    """Класс шарика с позицией, скоростью, цветом и радиусом."""
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    radius: float = 15.0
    color: Color = None
    
    def __post_init__(self):
        if self.color is None:
            # Случайный цвет по умолчанию
            import random
            self.color = Color(
                random.randint(50, 255),
                random.randint(50, 255),
                random.randint(50, 255)
            )
    
    def get_position(self) -> Tuple[float, float]:
        """Возвращает текущую позицию шарика."""
        return (self.x, self.y)
    
    def distance_to(self, other: 'Ball') -> float:
        """Вычисляет расстояние до другого шарика."""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)
    
    def is_colliding(self, other: 'Ball') -> bool:
        """Проверяет, касается ли этот шарик другого."""
        distance = self.distance_to(other)
        return distance < (self.radius + other.radius)


class DeleteZone:
    """Зона на экране, где шарики можно удалить."""
    
    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def contains(self, ball: Ball) -> bool:
        """Проверяет, находится ли шарик в зоне удаления."""
        return (self.x <= ball.x <= self.x + self.width and
                self.y <= ball.y <= self.y + self.height)


class GameLogic:
    """Основной класс игровой логики."""
    
    def __init__(self, screen_width: float = 800, screen_height: float = 600):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.balls: List[Ball] = []
        self.inventory: List[Ball] = []
        self.delete_zone = DeleteZone(
            screen_width - 100,  # Правая часть экрана
            0,
            100,
            100
        )
        self.friction = 0.98  # Трение для замедления шариков
        self.gravity = 0.2  # Гравитация (опционально)
    
    def add_ball(self, x: float, y: float, color: Optional[Color] = None) -> Ball:
        """Добавляет новый шарик на экран."""
        ball = Ball(x, y, color=color)
        self.balls.append(ball)
        return ball
    
    def remove_ball(self, ball: Ball):
        """Удаляет шарик из игры."""
        if ball in self.balls:
            self.balls.remove(ball)
    
    def update(self, dt: float = 1.0):
        """
        Обновляет состояние игры.
        
        Args:
            dt: Дельта времени (можно использовать для плавной анимации)
        """
        # Обновляем позиции шариков
        for ball in self.balls:
            # Применяем скорость
            ball.x += ball.vx * dt
            ball.y += ball.vy * dt
            
            # Применяем гравитацию
            ball.vy += self.gravity * dt
            
            # Применяем трение
            ball.vx *= self.friction
            ball.vy *= self.friction
            
            # Обработка столкновений со стенами
            if ball.x - ball.radius < 0:
                ball.x = ball.radius
                ball.vx = -ball.vx * 0.7  # Отскок с потерей энергии
            elif ball.x + ball.radius > self.screen_width:
                ball.x = self.screen_width - ball.radius
                ball.vx = -ball.vx * 0.7
            
            if ball.y - ball.radius < 0:
                ball.y = ball.radius
                ball.vy = -ball.vy * 0.7
            elif ball.y + ball.radius > self.screen_height:
                ball.y = self.screen_height - ball.radius
                ball.vy = -ball.vy * 0.7
            
            # Проверка зоны удаления
            if self.delete_zone.contains(ball):
                self.remove_ball(ball)
        
        # Обработка касаний шариков (смешивание цветов)
        self._handle_ball_collisions()
    
    def _handle_ball_collisions(self):
        """Обрабатывает касания шариков и смешивает их цвета."""
        processed_pairs = set()
        
        for i, ball1 in enumerate(self.balls):
            for j, ball2 in enumerate(self.balls[i + 1:], start=i + 1):
                if ball1.is_colliding(ball2):
                    # Избегаем повторной обработки одной пары
                    pair_id = tuple(sorted([id(ball1), id(ball2)]))
                    if pair_id in processed_pairs:
                        continue
                    processed_pairs.add(pair_id)
                    
                    # Смешиваем цвета
                    new_color = self._mix_colors(ball1.color, ball2.color)
                    ball1.color = new_color
                    ball2.color = new_color
    
    def _mix_colors(self, color1: Color, color2: Color) -> Color:
        """
        Смешивает два цвета интересным способом.
        Белый цвет (близкий к белому) считается плохим результатом.
        
        Использует алгоритм смешивания, который создаёт яркие цвета,
        избегая блеклых/белых результатов.
        """
        # Используем нелинейное смешивание для более интересных результатов
        # Вместо простого среднего используем умножение и нормализацию
        
        # Вычисляем "яркость" каждого цвета
        brightness1 = (color1.r + color1.g + color1.b) / 3.0
        brightness2 = (color2.r + color2.g + color2.b) / 3.0
        
        # Смешиваем с учётом яркости (более яркие цвета имеют больший вес)
        total_brightness = brightness1 + brightness2
        if total_brightness < 0.1:
            total_brightness = 0.1
        
        weight1 = brightness1 / total_brightness
        weight2 = brightness2 / total_brightness
        
        # Нелинейное смешивание компонентов
        r = int((color1.r * weight1 + color2.r * weight2) * 0.8 + 
                (color1.r * color2.r / 255.0) * 0.2)
        g = int((color1.g * weight1 + color2.g * weight2) * 0.8 + 
                (color1.g * color2.g / 255.0) * 0.2)
        b = int((color1.b * weight1 + color2.b * weight2) * 0.8 + 
                (color1.b * color2.b / 255.0) * 0.2)
        
        # Усиливаем насыщенность, чтобы избежать блеклых цветов
        # Находим максимальный компонент
        max_component = max(r, g, b, 1)
        
        # Нормализуем и усиливаем
        if max_component < 128:
            # Если цвет слишком тёмный, делаем его ярче
            scale = 255 / max(max_component, 1)
            r = min(255, int(r * scale * 0.7))
            g = min(255, int(g * scale * 0.7))
            b = min(255, int(b * scale * 0.7))
        else:
            # Усиливаем контраст
            r = min(255, int(r * 1.1))
            g = min(255, int(g * 1.1))
            b = min(255, int(b * 1.1))
        
        # Проверяем, не получился ли белый/блеклый цвет
        # Если все компоненты близки друг к другу и высокие - это плохо
        avg = (r + g + b) / 3.0
        variance = abs(r - avg) + abs(g - avg) + abs(b - avg)
        
        if variance < 30 and avg > 200:
            # Слишком близко к белому - делаем более насыщенным
            # Смещаем в сторону более яркого компонента
            if r > g and r > b:
                r = min(255, int(r * 1.2))
                g = max(0, int(g * 0.7))
                b = max(0, int(b * 0.7))
            elif g > r and g > b:
                g = min(255, int(g * 1.2))
                r = max(0, int(r * 0.7))
                b = max(0, int(b * 0.7))
            else:
                b = min(255, int(b * 1.2))
                r = max(0, int(r * 0.7))
                g = max(0, int(g * 0.7))
        
        return Color(r, g, b)
    
    def suck_ball(self, mouse_x: float, mouse_y: float, radius: float = 50.0) -> Optional[Ball]:
        """
        "Всасывает" ближайший шарик в инвентарь.
        
        Args:
            mouse_x: X координата мыши
            mouse_y: Y координата мыши
            radius: Радиус зоны всасывания
        
        Returns:
            Шарик, который был всасан, или None
        """
        closest_ball = None
        min_distance = radius
        
        for ball in self.balls:
            dx = ball.x - mouse_x
            dy = ball.y - mouse_y
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance < min_distance:
                min_distance = distance
                closest_ball = ball
        
        if closest_ball:
            self.balls.remove(closest_ball)
            self.inventory.append(closest_ball)
            return closest_ball
        
        return None
    
    def spit_ball(self, mouse_x: float, mouse_y: float, 
                  velocity: float = 5.0) -> Optional[Ball]:
        """
        "Выплёвывает" шарик из инвентаря обратно на экран.
        
        Args:
            mouse_x: X координата мыши (позиция выплёвывания)
            mouse_y: Y координата мыши (позиция выплёвывания)
            velocity: Начальная скорость шарика
        
        Returns:
            Шарик, который был выплюнут, или None
        """
        if not self.inventory:
            return None
        
        # Берём последний добавленный шарик
        ball = self.inventory.pop()
        
        # Устанавливаем позицию
        ball.x = mouse_x
        ball.y = mouse_y
        
        # Даём случайную начальную скорость
        import random
        angle = random.uniform(0, 2 * math.pi)
        ball.vx = math.cos(angle) * velocity
        ball.vy = math.sin(angle) * velocity
        
        # Добавляем обратно на экран
        self.balls.append(ball)
        return ball
    
    def get_ball_at_position(self, x: float, y: float, radius: float = 20.0) -> Optional[Ball]:
        """
        Находит шарик в указанной позиции.
        
        Args:
            x: X координата
            y: Y координата
            radius: Радиус поиска
        
        Returns:
            Найденный шарик или None
        """
        for ball in self.balls:
            dx = ball.x - x
            dy = ball.y - y
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance < radius:
                return ball
        
        return None
    
    def get_inventory_size(self) -> int:
        """Возвращает количество шариков в инвентаре."""
        return len(self.inventory)
    
    def clear_inventory(self):
        """Очищает инвентарь."""
        self.inventory.clear()
    
    def set_screen_size(self, width: float, height: float):
        """Устанавливает размер экрана."""
        self.screen_width = width
        self.screen_height = height
        # Обновляем позицию зоны удаления
        self.delete_zone = DeleteZone(
            width - 100,
            0,
            100,
            100
        )

