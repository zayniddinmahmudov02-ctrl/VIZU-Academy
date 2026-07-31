class UserRole:

    SUPER_ADMIN = "SUPER_ADMIN"

    ADMIN = "ADMIN"

    CONTENT_MANAGER = "CONTENT_MANAGER"

    PAYMENT_MANAGER = "PAYMENT_MANAGER"

    SUPPORT = "SUPPORT"

    TEACHER = "TEACHER"

    STUDENT = "STUDENT"

    ADMIN_PANEL_ROLES = {
        SUPER_ADMIN,
        ADMIN,
        CONTENT_MANAGER,
        PAYMENT_MANAGER,
        SUPPORT,
        TEACHER,
    }

    # Every valid value for User.role — used to validate role-assignment
    # input so a typo/garbage string can't be written to the column.
    ALL_ROLES = ADMIN_PANEL_ROLES | {STUDENT}
