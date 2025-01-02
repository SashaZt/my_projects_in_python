<?php

add_action('rest_api_init', 'ap_handle_new_property_meta');
function ap_handle_new_property_meta() {
    register_rest_field(
        'property',
        'property_meta',
        [
            'get_callback'    => function($object) {
                $raw_data = get_post_meta($object['id'], 'property_meta', true);
                if (is_string($raw_data)) {
                    $decoded = json_decode($raw_data, true);
                    if (json_last_error() === JSON_ERROR_NONE) {
                        return $decoded;
                    }
                }
                return $raw_data;
            },
            'update_callback' => function($value, $object) {
                if (!current_user_can('edit_posts')) {
                    return new WP_Error('rest_forbidden', __('You do not have permission to update this field'), ['status' => 403]);
                }
                if (!is_array($value)) {
                    return new WP_Error('rest_invalid_param', __('The value must be a JSON object (array)'));
                }

                // Получаем текущее значение property_meta
                $current_value = get_post_meta($object->ID, 'property_meta', true);
                $current_value = $current_value ? json_decode($current_value, true) : [];

                // Универсальное объединение текущих и новых значений
                foreach ($value as $key => $new_value) {
                    if (is_array($new_value)) {
                        // Если новое значение массив, объединяем с текущим
                        $current_value[$key] = array_merge(
                            isset($current_value[$key]) && is_array($current_value[$key]) ? $current_value[$key] : [],
                            $new_value
                        );
                    } else {
                        // Если новое значение строка, заменяем текущее
                        $current_value[$key] = $new_value;
                    }
                }

                // Сохраняем обновленные данные в property_meta
                update_post_meta($object->ID, 'property_meta', wp_json_encode($current_value));

                // Работа с fave_property_images
                if (isset($value['fave_property_images']) && is_array($value['fave_property_images'])) {
                    $images_arr = get_post_meta($object->ID, 'fave_property_images', true);
                    $merged_images = array_merge(
                        is_array($images_arr) ? $images_arr : [],
                        $value['fave_property_images']
                    );

                    // Сохраняем изображения
                    foreach ($merged_images as $image) {
                        add_post_meta($object->ID, 'fave_property_images', $image, false);
                    }
                }

                // Работа с fave_property_price
                if (isset($value['fave_property_price'])) {
                    update_post_meta($object->ID, 'fave_property_price', $value['fave_property_price']);
                }

                // Работа с fave_property_size
                if (isset($value['fave_property_size'])) {
                    update_post_meta($object->ID, 'fave_property_size', $value['fave_property_size']);
                }

                // Работа с fave_property_bedrooms
                if (isset($value['fave_property_bedrooms'])) {
                    update_post_meta($object->ID, 'fave_property_bedrooms', $value['fave_property_bedrooms']);
                }

                // Работа с fave_property_bathrooms
                if (isset($value['fave_property_bathrooms'])) {
                    update_post_meta($object->ID, 'fave_property_bathrooms', $value['fave_property_bathrooms']);
                }

                // Работа с fave_property_year
                if (isset($value['fave_property_year'])) {
                    update_post_meta($object->ID, 'fave_property_year', $value['fave_property_year']);
                }

                // Работа с fave_property_map_address
                if (isset($value['fave_property_map_address'])) {
                    update_post_meta($object->ID, 'fave_property_map_address', $value['fave_property_map_address']);
                }

                return $current_value;
            },
            'schema' => [
                'description' => __('Property meta fields object'),
                'type'        => 'object',
            ],
        ]
    );
}
