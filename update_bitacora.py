"""
File used executed within a cron tab

Such a file import the update_bitacora_manager.py and executes the main function that update bitacora
file.
"""

import update_bitacora_manager


def main() -> None:
    """ Main function to be executed when the .py file will be executed directly"""
    update_bitacora_manager.main('Last week')
    print("=============== Bitacora Updated ================")


if __name__ == "__main__":
    main()
