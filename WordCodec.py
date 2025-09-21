# -*- coding: utf-8 -*-
# pyarmor gen -O dist WordCodec.py
# pyinstaller dist/WordCodec.py --onefile --icon=icon.ico --add-data "dist/pyarmor_runtime_000000;pyarmor_runtime_000000"

import bz2
import os
from typing import Set, List


class WordCodec:
    def __init__(self):
        self.words: Set[str] = set()
        self.filename = "words.txt"
        self.output_filename = "words.xor"
        self.__key = "uStgURnWUEYbcKsfbvVuWRSnZz56bWv9lje/tUSLbJ4="

    def encode(self, data: bytes) -> None:
        """Кодирует данные с помощью XOR и сжимает их"""
        try:
            key_bytes = self.__key.encode("utf-8")
            encrypted_data = bytearray()

            for i, byte in enumerate(data):
                encrypted_data.append(byte ^ key_bytes[i % len(key_bytes)])

            with open(self.output_filename, "wb") as file:
                file.write(bz2.compress(encrypted_data))

            print(f"Данные успешно закодированы и сохранены в {self.output_filename}")

        except Exception as e:
            print(f"Ошибка при кодировании: {e}")

    def decode(self) -> Set[str]:
        """Декодирует данные из файла"""
        if not os.path.exists(self.output_filename):
            print(f"Файл {self.output_filename} не найден")
            return set()

        try:
            with open(self.output_filename, "rb") as file:
                compressed = file.read()

            # Распаковываем bz2
            data = bz2.decompress(compressed)

            # Расшифровываем XOR
            key_bytes = self.__key.encode("utf-8")
            decrypted_data = bytearray()

            for i, byte in enumerate(data):
                decrypted_data.append(byte ^ key_bytes[i % len(key_bytes)])

            # Декодируем в строки
            decoded_text = decrypted_data.decode("utf-8")
            return set(
                line.strip() for line in decoded_text.splitlines() if line.strip()
            )

        except Exception as e:
            print(f"Ошибка при декодировании: {e}")
            return set()

    def _is_valid_russian_word(self, word: str) -> bool:
        """Проверяет, является ли слово корректным русским словом"""
        if len(word) > 20:
            return False

        # Проверяем, что все символы - русские буквы
        return all("а" <= ch.lower() <= "я" or ch.lower() == "ё" for ch in word)

    def _load_words_from_file(self) -> List[str]:
        """Загружает слова из файла"""
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                return [word.strip() for word in f.read().splitlines() if word.strip()]
        except FileNotFoundError:
            print(f"Файл {self.filename} не найден!")
            return []
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
            return []

    def process(self) -> None:
        """Обрабатывает слова из файла и объединяет с существующими"""
        # Загружаем существующие слова
        self.words = self.decode()

        # Загружаем новые слова из файла
        new_words = self._load_words_from_file()
        if not new_words:
            return

        # Фильтруем и добавляем валидные слова
        valid_words = []
        invalid_words = []

        for word in new_words:
            if self._is_valid_russian_word(word):
                valid_words.append(word)
            else:
                invalid_words.append(word)
                if len(word) > 20:
                    print(f"Слишком длинное слово (пропущено): {word}")
                else:
                    print(f"Недопустимые символы в слове (пропущено): {word}")

        # Добавляем валидные слова к существующим
        self.words.update(valid_words)

        # Конвертируем в отсортированный список
        sorted_words = sorted(list(self.words))

        print(f"Обработано {len(valid_words)} новых слов")
        print(f"Пропущено {len(invalid_words)} невалидных слов")
        print(f"Общее количество уникальных слов: {len(sorted_words)}")

        # Сохраняем закодированные данные
        words_text = "\n".join(sorted_words)
        self.encode(words_text.encode("utf-8"))

    def get_words_list(self) -> List[str]:
        """Возвращает список всех слов"""
        return sorted(list(self.words))

    def add_word(self, word: str) -> bool:
        """Добавляет одно слово"""
        word = word.strip()
        if self._is_valid_russian_word(word):
            self.words.add(word)
            return True
        return False

    def remove_word(self, word: str) -> bool:
        """Удаляет слово"""
        if word in self.words:
            self.words.remove(word)
            return True
        return False

    def save_words(self) -> None:
        """Сохраняет текущий набор слов"""
        if self.words:
            words_text = "\n".join(sorted(self.words))
            self.encode(words_text.encode("utf-8"))
            print(f"Сохранено {len(self.words)} слов в {self.output_filename}")
        else:
            print("Нет слов для сохранения")

    def run(self) -> None:
        """Главный метод запуска"""
        # Устанавливаем кодировку для Windows
        if os.name == "nt":
            os.system("chcp 65001 > nul")

        print("=== WordCodec - Обработка файла ===")
        self.process()

        # Показываем статистику
        words_list = self.get_words_list()
        if words_list:
            print(f"\nПервые 10 слов: {words_list[:10]}")
            if len(words_list) > 10:
                print(f"... и еще {len(words_list) - 10} слов")

        input("\nНажмите Enter для завершения...")


def main():
    """Точка входа в программу"""
    codec = WordCodec()
    codec.run()


if __name__ == "__main__":
    main()
