# when redefining a local variable, it should not be overwritten.
# [correct] local _abc = 123 -- _abc = 123
#[!correct] local _abc = 123 -- _abc = 123 # Redefinition.
# It should be:
# [correct] local _abc = 123 -- _abc = 123
# [correct] _abc = 123 -- _abc = 123 # Redefinition.

_abc = 123
_abc = 234
abc = "Hello, "
abc = "World! "