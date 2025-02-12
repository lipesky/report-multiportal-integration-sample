# Sample Multiportal Report Server

A simple application(POC) for extending reporting features of Multi Portal dashboard solution, giving powerful insights. It uses FastAPI, OpenpyXl and SQLite.

OBS: As it is a POC (proof of concept), there are many points that can be improoved. That will be detailed in "Improvements" section.

## How it works

- Perform a search for all vehicles
- Retrieves data for each vehicle sequentially (here we need to perform each fetch sequentially to avoid api block), taking care of authentication, retrying etc.
- Model classes have a fucntion to extract custom data stored in another fields, this case we have custom information about branches and shifts in field 'Descricao' in model in a custom format.
- After parsed, filtered and formatted all information, passes not next step, wich can be:
    - return in json format
    - return in xlsx format

## Possible improvements
- use a robust SGBD
- check parallelism with several api keys
- standardize custom formats
- add another export formats, specially pdf