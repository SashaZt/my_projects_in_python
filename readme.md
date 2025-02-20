## **1. Создание SIP-аккаунта (Extensions) в FreePBX**

1. **Открываем веб-интерфейс FreePBX**
   * В браузере перейдите по адресу вашего FreePBX (например, `http://92.112.181.197/`).
   * Войдите в систему под администраторской учетной записью.
2. **Переходим в раздел Extensions**
   * В меню слева выберите   **Applications → Extensions** .
   * Нажмите **"Add Extension"** и выберите  **Add New SIP [chan_pjsip] Extension** .
3. **Настраиваем Extension**
   * **User Extension** : Введите номер внутреннего абонента (например, `101`).
   * **Display Name** : Укажите имя пользователя (например, `Office Phone`).
   * **Secret (Пароль)** : Сгенерируется пароль автоматически.
4. **Сохраняем и применяем настройки**
   * Нажмите   **Submit** , затем **Apply Config** (красная кнопка сверху).

---

## **2. Подключение MicroSIP к FreePBX**

### **Открываем настройки учетной записи**

1. В MicroSIP нажмите **"Настройки"** (иконка шестеренки).
   * Нажмите   **"Добавить"** , чтобы создать новый SIP-аккаунт.
2. **Заполняем параметры SIP-аккаунта**
   * **Account Name (Имя аккаунта)** : любое удобное название (например, `92.112.181.197`).
   * **SIP-сервер** : IP-адрес `92.112.181.197`.
   * **Порт** : `5060` (если PJSIP, то `5060`; если CHAN SIP, то `5160`).
   * **Пользователь** : номер Extension (например, `101`).
   * **Пароль** : тот, что указали в FreePBX при создании Extension.
   * **Логин (SIP Login)** : такой же, как номер Extension (например, `101`).
3. **Сохраняем настройки и проверяем подключение**
   * Нажмите   **Сохранить** .
   * В главном окне MicroSIP в правом нижнем углу должен появиться статус   **"Онлайн"** . Если написано   **"Ошибка регистрации"** , проверьте введенные данные.
