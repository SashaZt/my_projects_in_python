# # 1. Создаем класс
# class Person:
#     def __init__(self, name, age):  # 2. Создаем атрибуты в конструкторе
#         self.name = name
#         self.age = age

#     def introduce(self):  # 3. Создаем метод
#         print(f"Привет, меня зовут {self.name} и мне {self.age} лет.")


# # 4. Создаем объект класса
# person1 = Person("Иван", 30)

# # 5. Вызываем метод объекта
# person1.introduce()  # Выведет: Привет, меня зовут Иван и мне 30 лет.


# class Person:

#     def __init__(self, name, age) -> None:
#         self.name = name
#         self.age = age

#     def print_name_and_age(self):
#         print(f"Привет, меня зовут {self.name}, мне {self.age}")

#     def is_adult(self):
#         if self.age >= 18:
#             return "Совершеннолетний"
#         else:
#             return "Несовершеннолетний"

#     def celebrate_birthday(self):
#         self.age += 1
#         print(f"С днем рождения, {self.name}! Теперь тебе {self.age} лет.")


# person = Person("Аня", 17)
# print(person.is_adult())  # Должно вывести: Несовершеннолетний
# person.celebrate_birthday()  # Должно вывести: С днем рождения, Аня! Теперь тебе 18 лет.
# print(person.is_adult())  # Должно вывести: Совершеннолетний


class Person:
    def __init__(self, name, age):
        self.name = name
        self._age = None  # Инкапсулируем атрибут с одним подчеркиванием
        self.age = age  # Используем метод-сеттер для установки значения

    # Геттер для атрибута `_age`
    @property
    def age(self):
        return self._age

    # Сеттер для атрибута `_age`
    @age.setter
    def age(self, value):
        if value >= 0:
            self._age = value
        else:
            raise ValueError("Возраст не может быть отрицательным")


# Пример использования
person = Person("Иван", 30)
print(person.age)  # Выведет: 30

person.age = 25  # Корректное значение
print(person.age)  # Выведет: 25

# person.age = -5  # Приведет к исключению: ValueError: Возраст не может быть отрицательным
