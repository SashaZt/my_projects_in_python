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

                // Объединяем текущие и новые значения
                $merged_value = array_merge(
                    is_array($current_value) ? $current_value : [],
                    is_array($value) ? $value : []
                );
                update_post_meta($object->ID, 'property_meta', wp_json_encode($merged_value));

                // Работа с fave_property_images
                $images_arr = get_post_meta($object->ID, 'fave_property_images');
                $merged_images = array_merge(
                    is_array($images_arr) ? $images_arr : [],
                    isset($value['fave_property_images']) && is_array($value['fave_property_images']) ? $value['fave_property_images'] : []
                );

                // Сохраняем изображения
                $array_to_save = [];
                foreach ($merged_images as $image) {
                    array_push($array_to_save, $image);
                }
                foreach ($array_to_save as $item) {
                    add_post_meta($object->ID, 'fave_property_images', $item, false);
                }
                return $merged_value;
            },
            'schema' => [
                'description' => __('Property meta fields object'),
                'type'        => 'object',
            ],
        ]
    );
}
