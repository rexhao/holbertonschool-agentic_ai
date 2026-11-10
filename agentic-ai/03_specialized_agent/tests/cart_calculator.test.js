const { calculateTotal } = require('../src/cart_calculator');

describe('calculateTotal', () => {
    it('should_return_zero_when_cart_is_empty', () => {
        // Arrange
        const items = [];

        // Act
        const result = calculateTotal(items);

        // Assert
        expect(result).toBe(0);
    });

    it('should_return_zero_when_items_is_null', () => {
        // Arrange
        const items = null;

        // Act
        const result = calculateTotal(items);

        // Assert
        expect(result).toBe(0);
    });

    it('should_return_zero_when_items_is_undefined', () => {
        // Arrange
        const items = undefined;

        // Act
        const result = calculateTotal(items);

        // Assert
        expect(result).toBe(0);
    });

    it('should_return_zero_when_items_is_not_an_array', () => {
        // Arrange
        const items = { price: 10, quantity: 1 };

        // Act
        const result = calculateTotal(items);

        // Assert
        expect(result).toBe(0);
    });

    it('should_return_zero_when_item_has_no_price', () => {
        // Arrange
        const items = [{ quantity: 3 }];

        // Act
        const result = calculateTotal(items);

        // Assert
        expect(result).toBe(0);
    });

    it('should_return_zero_when_price_is_zero', () => {
        // Arrange
        const items = [{ price: 0, quantity: 5 }];

        // Act
        const result = calculateTotal(items);

        // Assert
        expect(result).toBe(0);
    });

    it('should_return_zero_when_price_is_not_a_number', () => {
        // Arrange
        const items = [{ price: NaN, quantity: 2 }];

        // Act
        const result = calculateTotal(items);

        // Assert
        expect(result).toBe(0);
    });

    it('should_skip_items_without_a_price_when_other_lines_are_billable', () => {
        // Arrange
        const items = [{}, { price: 10, quantity: 1 }];

        // Act
        const result = calculateTotal(items);

        // Assert
        expect(result).toBe(12);
    });

    it('should_apply_twenty_percent_tax_when_tax_rate_is_omitted', () => {
        // Arrange
        const items = [{ price: 10, quantity: 2 }];

        // Act
        const result = calculateTotal(items);

        // Assert
        expect(result).toBe(24);
    });

    it('should_apply_no_discount_when_discount_is_omitted', () => {
        // Arrange
        const items = [{ price: 10, quantity: 2 }];
        const taxRate = 0;

        // Act
        const result = calculateTotal(items, taxRate);

        // Assert
        expect(result).toBe(20);
    });

    it('should_apply_custom_tax_rate_when_tax_rate_is_provided', () => {
        // Arrange
        const items = [{ price: 100, quantity: 1 }];
        const taxRate = 0.05;
        const discount = 0;

        // Act
        const result = calculateTotal(items, taxRate, discount);

        // Assert
        expect(result).toBe(105);
    });

    it('should_charge_the_untaxed_subtotal_when_tax_rate_is_zero', () => {
        // Arrange
        const items = [{ price: 10, quantity: 2 }];
        const taxRate = 0;
        const discount = 0;

        // Act
        const result = calculateTotal(items, taxRate, discount);

        // Assert
        expect(result).toBe(20);
    });

    it('should_charge_the_untaxed_subtotal_when_tax_rate_is_null', () => {
        // Arrange
        const items = [{ price: 10, quantity: 1 }];
        const taxRate = null;
        const discount = 0;

        // Act
        const result = calculateTotal(items, taxRate, discount);

        // Assert
        expect(result).toBe(10);
    });

    it('should_sum_every_line_when_cart_contains_several_items', () => {
        // Arrange
        const items = [
            { price: 10, quantity: 1 },
            { price: 5, quantity: 2 }
        ];

        // Act
        const result = calculateTotal(items);

        // Assert
        expect(result).toBe(24);
    });

    it('should_default_quantity_to_one_when_quantity_is_missing', () => {
        // Arrange
        const items = [{ price: 10 }];

        // Act
        const result = calculateTotal(items);

        // Assert
        expect(result).toBe(12);
    });

    it('should_default_quantity_to_one_when_quantity_is_zero', () => {
        // Arrange
        const items = [{ price: 10, quantity: 0 }];

        // Act
        const result = calculateTotal(items);

        // Assert
        expect(result).toBe(12);
    });

    it('should_default_quantity_to_one_when_quantity_is_null', () => {
        // Arrange
        const items = [{ price: 15, quantity: null }];

        // Act
        const result = calculateTotal(items);

        // Assert
        expect(result).toBe(18);
    });

    it('should_exclude_the_line_when_quantity_is_negative', () => {
        // Arrange
        const items = [
            { price: 10, quantity: -3 },
            { price: 5, quantity: 1 }
        ];

        // Act
        const result = calculateTotal(items);

        // Assert
        expect(result).toBe(6);
    });

    it('should_exclude_the_line_when_price_is_negative', () => {
        // Arrange
        const items = [
            { price: -5, quantity: 2 },
            { price: 10, quantity: 1 }
        ];

        // Act
        const result = calculateTotal(items);

        // Assert
        expect(result).toBe(12);
    });

    it('should_subtract_discount_before_tax_when_both_are_provided', () => {
        // Arrange
        const items = [{ price: 100, quantity: 1 }];
        const taxRate = 0.20;
        const discount = 20;

        // Act
        const result = calculateTotal(items, taxRate, discount);

        // Assert
        expect(result).toBe(96);
    });

    it('should_apply_discount_then_tax_when_line_total_is_fractional', () => {
        // Arrange
        const items = [{ price: 9.99, quantity: 3 }];
        const taxRate = 0.20;
        const discount = 5;

        // Act
        const result = calculateTotal(items, taxRate, discount);

        // Assert
        expect(result).toBe(29.96);
    });

    it('should_return_zero_when_discount_equals_subtotal', () => {
        // Arrange
        const items = [{ price: 10, quantity: 1 }];
        const taxRate = 0.20;
        const discount = 10;

        // Act
        const result = calculateTotal(items, taxRate, discount);

        // Assert
        expect(result).toBe(0);
    });

    it('should_return_zero_when_discount_exceeds_subtotal', () => {
        // Arrange
        const items = [{ price: 10, quantity: 1 }];
        const taxRate = 0.20;
        const discount = 50;

        // Act
        const result = calculateTotal(items, taxRate, discount);

        // Assert
        expect(result).toBe(0);
    });

    it('should_increase_the_taxable_amount_when_discount_is_negative', () => {
        // Arrange
        const items = [{ price: 10, quantity: 1 }];
        const taxRate = 0.20;
        const discount = -5;

        // Act
        const result = calculateTotal(items, taxRate, discount);

        // Assert
        expect(result).toBe(18);
    });

    it('should_round_to_two_decimal_euros_when_tax_creates_extra_digits', () => {
        // Arrange
        const items = [{ price: 19.99, quantity: 3 }];
        const taxRate = 0.20;
        const discount = 0;

        // Act
        const result = calculateTotal(items, taxRate, discount);

        // Assert
        expect(result).toBe(71.96);
    });

    it('should_round_half_up_when_the_third_decimal_is_five_or_higher', () => {
        // Arrange
        const items = [{ price: 10.015, quantity: 1 }];
        const taxRate = 0;
        const discount = 0;

        // Act
        const result = calculateTotal(items, taxRate, discount);

        // Assert
        expect(result).toBe(10.02);
    });

    it('should_round_down_when_the_third_decimal_is_below_five', () => {
        // Arrange
        const items = [{ price: 10.004, quantity: 1 }];
        const taxRate = 0;
        const discount = 0;

        // Act
        const result = calculateTotal(items, taxRate, discount);

        // Assert
        expect(result).toBe(10);
    });

    it('should_round_to_two_decimals_when_subtotal_has_a_binary_float_error', () => {
        // Arrange
        const items = [
            { price: 0.1, quantity: 1 },
            { price: 0.2, quantity: 1 }
        ];
        const taxRate = 0;
        const discount = 0;

        // Act
        const result = calculateTotal(items, taxRate, discount);

        // Assert
        expect(result).toBe(0.3);
    });

    it('should_round_the_discounted_total_when_discount_is_fractional', () => {
        // Arrange
        const items = [{ price: 10, quantity: 1 }];
        const taxRate = 0;
        const discount = 0.333;

        // Act
        const result = calculateTotal(items, taxRate, discount);

        // Assert
        expect(result).toBe(9.67);
    });

    it('should_coerce_numeric_strings_when_price_and_quantity_are_numeric_strings', () => {
        // Arrange
        const items = [{ price: '10', quantity: '2' }];

        // Act
        const result = calculateTotal(items);

        // Assert
        expect(result).toBe(24);
    });
});
