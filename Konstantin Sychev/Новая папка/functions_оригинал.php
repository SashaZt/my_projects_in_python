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

                $current_value = get_post_meta($object->ID, 'property_meta', true);
                $images_arr = get_post_meta($object->ID, 'fave_property_images');

                $current_value = $current_value ? json_decode($current_value, true) : [];
                $merged_value = array_merge($current_value, $value);
                update_post_meta($object->ID, 'property_meta', wp_json_encode($merged_value));
                $merged_images = [];
                if(!empty($images_arr) && is_array($images_arr)) {
                    $merged_images = array_merge($images_arr, $value['fave_property_images']);
                } else {
                    $merged_images = $value['fave_property_images'];
                }
                $array_to_save = [];
                foreach($merged_images as $image) {
                    array_push($array_to_save, $image);
                }
                foreach ( $array_to_save as $item ) {
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
