request_timeout (30)
Максимальное время ожидания (в секундах) для выполнения HTTP-запроса к целевому сайту или API.
result_timeout (60)
Максимальное время ожидания (в секундах) для получения результата обработки задания (например, HTML-контента страницы) от сервиса скрапинга.
max_job_check_attempts (10)
Максимальное количество попыток проверки статуса задания.
job_check_interval (10)
Интервал времени (в секундах) между попытками проверки статуса задания.
max_submit_retries (3)
Максимальное количество попыток повторной отправки задания в случае неудачи.
check_cycle_interval (30)
Интервал времени (в секундах) между циклами проверки и обработки всех активных заданий.
max_parallel_checks (5)
Максимальное количество заданий, которые могут проверяться параллельно.
max_parallel_submits (10)
Максимальное количество заданий, которые могут отправляться параллельно.
check_batch_size (500)
Размер пакета заданий для параллельной обработки.
