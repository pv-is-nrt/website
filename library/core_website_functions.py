# ==================================================================== #
#
#    Title: Website Core Functions
#    Author: Prateek Verma
#    Courtesy: None
#    Created on: Apr 12, 2022
#
# ==================================================================== #


# ============================================================================ #
#    DATABASE RELATED
# ============================================================================ #

def insert_dict_to_model(dict:dict, model:object):
    """
    This function inserts a dictionary into a model. The model must have already been instantiated.
    """
    # iterate through the dictionary and set the values
    for k, v in dict.items():
        setattr(model, k, v)
        # save the model
        model.save()


# ============================================================================ #
#    ANALYTICS
# ============================================================================ #

def get_user_info(request, model:object):
    """
    This function returns the user's information. This uses the model fields to gather the required information. NOTE that the model field names must match the HTTP etc. request names.

    RETURNS:
    A dictionary containing the user's information.

    NOTE: At this time, parsing HTTP_USER_AGENT is dependent on parsing of inconsistent user agents and requires use of a library, so I am not implementing it. Additionally, getting country, city from IP is also seemingly dependent on a library, so I am not implementing it either. These can be added later if necessary.
    """

    if not model:
        return None # fail silently

    model_fields = model._meta.get_fields() # returns a tuple of fields
    # get names from fields
    model_field_names = [field.name for field in model_fields]

    # initialize a dictionary to hold user information
    info = {}

    # for each field_name, obtain the meta information
    # NOTE: make sure to exclude field_names in models that do not correspond to user_info returned by the request
    # EXCLUDE: id, visited_page, timestamp
    for field_name in model_field_names:
        # these below field names will not have a corresponding HTTP request
        if field_name not in ['id', 'visited_page', 'timestamp']:
            info[field_name] = request.META.get(field_name.upper())
    
    return info


def add_user_info_to_database(model:object, request:object, visitedPage:str):
    """
    This function adds the user's information to the database. The model must have already been instantiated. Does not log visits from localhost, i.e., 127.0.0.1.
    It is dependent on two helper functions: one that generates user_info (dict) from the model fields and the other that adds the user_info to the database.

    RETURNS:
    Nothing.

    TODO: Try to see if you can simplify the get_user_info function. Maybe we don't need to specify which fields to ignore, coz the model save method is probably doing that.

    """

    # add the page to the user_info
    user_info = get_user_info(request, model)
    user_info['visited_page'] = visitedPage

    # add the dict to the database. See the helper functions for details
    # Ony if the visit is not by the 127.0.0.1
    if request.META.get('REMOTE_ADDR') != '127.0.0.1':
        insert_dict_to_model(user_info, model)
    