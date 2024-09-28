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


class Person:

    def __init__(self, name, age) -> None:
        self.name = name
        self.age = age

    def print_name_and_age(self):
        print(f"Привет, меня зовут {self.name}, мне {self.age}")

    def is_adult(self):
        if self.age >= 18:
            return "Совершеннолетний"
        else:
            return "Несовершеннолетний"

    def celebrate_birthday(self):
        self.age += 1
        print(f"С днем рождения, {self.name}! Теперь тебе {self.age} лет.")


person = Person("Аня", 17)
print(person.is_adult())  # Должно вывести: Несовершеннолетний
person.celebrate_birthday()  # Должно вывести: С днем рождения, Аня! Теперь тебе 18 лет.
print(person.is_adult())  # Должно вывести: Совершеннолетний
