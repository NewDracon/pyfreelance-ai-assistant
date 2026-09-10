INSERT INTO orders (id, external_id, title, description, url, site_name)
VALUES (gen_random_uuid(), 'test_notify', 'Разработать парсер на Python',
        'Нужен скрипт для сбора данных', 'https://example.com/1', 'test');
