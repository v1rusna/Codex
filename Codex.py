# -*- coding: utf-8 -*-
import os, random, shutil, bz2, collections, time


class ImprovedCodexGame:
    def __init__(self):
        self.version = "12.09.2025"

        self.__word = None
        self._guessed = {}
        self.__attempts = []
        self.__all_indices = collections.defaultdict(list)
        self.__used_count = collections.defaultdict(int)
        self.__size = shutil.get_terminal_size(fallback=(80, 24))
        self.__width = self.__size.columns
        self.__height = self.__size.lines

        # Улучшенная система очков
        self._base_points = 1000
        self._current_points = self._base_points
        self._hints = 3
        self._start_time = None
        self._combo_count = 0
        self._max_combo = 0
        self._perfect_positions = 0
        self._total_correct_letters = 0
        self._attempt_penalties = 0

        # Бонусы и штрафы
        self.SCORING = {
            "exact_match": 15,
            "partial_match": 5,
            "wrong_letter": -8,
            "attempt_penalty": -25,
            "hint_penalty": -50,
            "time_bonus_threshold": 180,  # секунд
            "combo_multiplier": 1.5,
            "speed_bonus_max": 200,
            "perfect_word_bonus": 100,
        }

    def random_word(self) -> str:
        return random.choice(self.decrypt("words.xor")).strip().lower()

    def clear(self):
        os.system("cls" if os.name == "nt" else "clear")

    def pause(self):
        input("Нажмите Enter для продолжения...")

    def run(self):
        self._start_time = time.time()
        self.__word = self.random_word()

        for char in self.__word:
            self._guessed[char] = False
        for i, char in enumerate(self.__word):
            self.__all_indices[char].append(i)

        self._game_cycle()

    def _game_cycle(self):
        while True:
            self._display_info()
            text = self._input()

            if text == self.__word:
                # Бонус за победу
                self._current_points += self.SCORING["perfect_word_bonus"]
                break

            # Сбрасываем счетчики перед обработкой новой попытки
            self.__used_count = collections.defaultdict(int)
            new_word = []
            attempt_correct_positions = 0

            for i, char in enumerate(text):
                result, is_exact = self._char_processing(char, i)
                new_word.append(result)
                if is_exact:
                    attempt_correct_positions += 1

            # Система комбо
            if attempt_correct_positions > 0:
                self._combo_count += 1
                self._max_combo = max(self._max_combo, self._combo_count)

                # Бонус за комбо
                if self._combo_count >= 3:
                    combo_bonus = int(
                        attempt_correct_positions
                        * self.SCORING["exact_match"]
                        * (self.SCORING["combo_multiplier"] - 1)
                    )
                    self._current_points += combo_bonus
            else:
                self._combo_count = 0

            self._perfect_positions += attempt_correct_positions

            user_word = "".join(new_word)
            self.__attempts.append(user_word)

            # Штраф за попытку
            self._attempt_penalties += self.SCORING["attempt_penalty"]
            self._current_points += self.SCORING["attempt_penalty"]

            print(f"> {user_word}")

        self._end_game()

    def _input(self) -> str:
        text = input("> ").strip().lower()

        if text == "exit":
            print("Загаданное слово было:", self.__word)
            self.pause()
            raise KeyboardInterrupt

        if text == "?" and self._hints > 0:
            self._hints -= 1
            self._current_points += self.SCORING["hint_penalty"]

            # Открываем случайную неугаданную букву
            unguessed_chars = [char for char in self.__word if not self._guessed[char]]
            if unguessed_chars:
                char_to_reveal = random.choice(unguessed_chars)
                self._guessed[char_to_reveal] = True

        return text[: len(self.__word)]

    def _char_processing(self, char: str, i: int) -> tuple[str, bool]:
        """
        Обрабатывает символ и возвращает его с соответствующим ANSI-форматированием.

        Returns:
            tuple: (formatted_char, is_exact_match)
        """
        # ANSI коды
        ANSI_CODES = {
            "exact_match": "46",  # Точное совпадение (зеленый фон)
            "partial_match": "220",  # Частичное совпадение (желтый)
            "no_match": "1",  # Нет совпадения (жирный)
        }

        is_exact = False

        if char in self.__word:
            idx_list = self.__all_indices[char]
            used_count = self.__used_count[char]

            if used_count < len(idx_list):
                index = idx_list[used_count]
                self.__used_count[char] += 1

                if index == i:
                    # Точное совпадение позиции
                    self._current_points += self.SCORING["exact_match"]
                    ansi_code = ANSI_CODES["exact_match"]
                    self._guessed[char] = True
                    self._total_correct_letters += 1
                    is_exact = True
                else:
                    # Символ есть в слове, но не в той позиции
                    self._current_points += self.SCORING["partial_match"]
                    ansi_code = ANSI_CODES["partial_match"]
            else:
                # Все вхождения символа уже использованы
                self._current_points += self.SCORING["partial_match"]
                ansi_code = ANSI_CODES["partial_match"]
        else:
            # Символа нет в слове
            self._current_points += self.SCORING["wrong_letter"]
            ansi_code = ANSI_CODES["no_match"]

        # Очки не могут быть отрицательными
        self._current_points = max(0, self._current_points)

        formatted_char = f"\u001b[38;5;{ansi_code}m{char}\u001b[0m"
        return formatted_char, is_exact

    def _calculate_final_score(self) -> dict:
        """Вычисляет финальный счет с учетом всех бонусов"""
        elapsed_time = time.time() - self._start_time

        # Бонус за скорость
        speed_bonus = 0
        if elapsed_time < self.SCORING["time_bonus_threshold"]:
            speed_bonus = int(
                self.SCORING["speed_bonus_max"]
                * (1 - elapsed_time / self.SCORING["time_bonus_threshold"])
            )

        # Бонус за эффективность (мало попыток)
        efficiency_bonus = max(0, (10 - len(self.__attempts)) * 20)

        # Бонус за комбо
        combo_bonus = self._max_combo * 25

        final_score = (
            self._current_points + speed_bonus + efficiency_bonus + combo_bonus
        )

        return {
            "base_score": self._current_points,
            "speed_bonus": speed_bonus,
            "efficiency_bonus": efficiency_bonus,
            "combo_bonus": combo_bonus,
            "final_score": final_score,
            "elapsed_time": elapsed_time,
        }

    def _get_performance_rank(self, score: int) -> str:
        """Определяет ранг игрока на основе очков"""
        if score >= 1200:
            return "🏆 МАСТЕР"
        elif score >= 1000:
            return "🥇 ЭКСПЕРТ"
        elif score >= 800:
            return "🥈 ПРОФИ"
        elif score >= 600:
            return "🥉 ЛЮБИТЕЛЬ"
        elif score >= 400:
            return "📚 НОВИЧОК"
        else:
            return "🤔 УЧЕНИК"

    def _end_game(self):
        self.clear()
        score_data = self._calculate_final_score()
        rank = self._get_performance_rank(score_data["final_score"])

        print("=" * 50)
        print("🎉 ПОЗДРАВЛЯЕМ! ВЫ УГАДАЛИ СЛОВО! 🎉")
        print("=" * 50)
        print()
        print(f"📝 Загаданное слово: {self.__word.upper()}")
        print(f"🎯 Количество попыток: {len(self.__attempts)}")
        print(f"⏱️  Время игры: {score_data['elapsed_time']:.1f} сек")
        print(f"🔥 Максимальное комбо: {self._max_combo}")
        print()
        print("📊 ДЕТАЛИЗАЦИЯ ОЧКОВ:")
        print("-" * 30)
        print(f"Базовые очки:      {score_data['base_score']:>6}")
        print(f"Бонус за скорость: {score_data['speed_bonus']:>6}")
        print(f"Бонус за попытки:  {score_data['efficiency_bonus']:>6}")
        print(f"Бонус за комбо:    {score_data['combo_bonus']:>6}")
        print("-" * 30)
        print(f"ИТОГОВЫЕ ОЧКИ:     {score_data['final_score']:>6}")
        print()
        print(f"🏅 ВАШ РАНГ: {rank}")
        print()
        print("📈 СТАТИСТИКА:")
        print(f"• Правильных позиций: {self._perfect_positions}")
        print(f"• Всего правильных букв: {self._total_correct_letters}")
        print(f"• Использовано подсказок: {3 - self._hints}")
        print()
        print("Все ваши попытки:")
        for i, attempt in enumerate(self.__attempts, 1):
            print(f"{i:2}. {attempt}")
        print()
        self.pause()

    def _display_info(self):
        self.clear()
        width = int(self.__width / 2 - len("| Codex Game |") / 2 - 1)
        print("<v1rus team>", end="")
        print("=" * (width - len("<v1rus team>")), end="")
        print("> Codex Game <", end="")
        print("=" * (width - len(f"<{self.version}>")), end="")
        print(f"<{self.version}>")

        # Информационная панель
        elapsed = time.time() - self._start_time if self._start_time else 0
        combo_display = f" 🔥x{self._combo_count}" if self._combo_count > 1 else ""

        print(
            f"📊 Очки: {self._current_points} | ⏱️  {elapsed:.0f}с | 💡 Подсказки: {self._hints}{combo_display}"
        )
        print(f"🎯 Слово: <{self._get_word()}>")
        print("-" * min(40, self.__width))

        # Показываем последние попытки
        for attempt in self.__attempts[-8:]:
            print(f"> {attempt}")

        if len(self.__attempts) > 8:
            print("...")

    def _get_word(self):
        word = []
        for char in self.__word:
            if self._guessed[char]:
                word.append(char)
            else:
                word.append("_")
        return " ".join(word)

    def decrypt(self, filename: str):
        with open(filename, "rb") as file:
            data = file.read()

        data = bz2.decompress(data)

        key_bytes = "uStgURnWUEYbcKsfbvVuWRSnZz56bWv9lje/tUSLbJ4=".encode("utf-8")
        decrypted_data = bytearray()

        for i, byte in enumerate(data):
            decrypted_data.append(byte ^ key_bytes[i % len(key_bytes)])

        return decrypted_data.decode("utf-8").splitlines()


if __name__ == "__main__":
    try:
        game = ImprovedCodexGame()
        game.run()
    except KeyboardInterrupt:
        print("\nВыход из игры.")
