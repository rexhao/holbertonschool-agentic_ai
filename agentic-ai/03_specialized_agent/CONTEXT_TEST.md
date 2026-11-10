## Response before clearing the context

The naming convention is:

`should_[EXPECTED_BEHAVIOR]_when_[CONDITION]`

The guideline example is `should_return_zero_when_cart_is_empty`. The name must be in English.

## Response obtained after the reset

Each `it()` or `test()` block must follow this pattern, written in English:

`should_[EXPECTED_BEHAVIOR]_when_[CONDITION]`

For example: `should_return_zero_when_cart_is_empty`

This comes from the Naming Convention section of `TESTING_GUIDELINES.md`.

## A brief note on the difference observed between the two situations.

Before the reset, the agent answered from the earlier chat and dropped some of the guideline context: it never said the rule applies to every `it()` or `test()` block, and it never named the Naming Convention section of `TESTING_GUIDELINES.md`. After the reset, it read the file again, so that missing context came back.
