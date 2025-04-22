import json

from policy_management import get_payment_policy, update_payment_policy


def check_payment_policy(policy_id):
    policy_data = get_payment_policy(policy_id)
    if policy_data:
        print("Данные политики оплаты:")
        print(json.dumps(policy_data, indent=4, ensure_ascii=False))
    else:
        print(f"Не удалось получить данные политики с ID {policy_id}")


def update_payment_policy_with_paypal(policy_id):
    update_data = {
        "name": "Standard Payment Policy DE",
        "description": "Standard payment policy for eBay Germany",
        "marketplaceId": "EBAY_DE",
        "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES", "default": False}],
        "paymentMethods": [
            {
                "paymentMethodType": "PAYPAL",
                "recipientAccountReference": {
                    "referenceId": "test@paypal.com",
                    "referenceType": "PAYPAL_EMAIL",
                },
            }
        ],
        "immediatePay": False,
    }

    success = update_payment_policy(policy_id, update_data)
    if success:
        print(f"Политика оплаты {policy_id} успешно обновлена с поддержкой PayPal")
    else:
        print(f"Не удалось обновить политику оплаты {policy_id}")


if __name__ == "__main__":
    policy_id = "6208882000"
    print("До обновления:")
    check_payment_policy(policy_id)
    update_payment_policy_with_paypal(policy_id)
    print("\nПосле обновления:")
    check_payment_policy(policy_id)
