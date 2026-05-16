from backend.utils.merch_variant_key import compute_merch_variant_key


def test_variant_key_fk_shape_with_extras():
    k = compute_merch_variant_key(
        color_id=1,
        size_id=2,
        attributes={'farbe': 'rot', 'extras': 'yes'},
    )
    assert k.startswith('fk|c=1|s=2|x:')


def test_variant_key_json_small():
    assert (
        compute_merch_variant_key(
            color_id=None, size_id=None, attributes={'foo': 'bar'}
        ).startswith('js|')
    )


def test_slugify_ascii_label_umlaut():
    from backend.utils.merch_variant_key import slugify_ascii_label

    assert 'oe' in slugify_ascii_label('Grösse')
