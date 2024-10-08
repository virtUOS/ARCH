## Populate the DB 

To populate the DB with a superuser, sample users and residential groups.

```
python manage.py populate_db --settings=arch.settings
```

## Create archive backup as a zipped file

- To create a zipped archive of all media files in archive group with id 1.

  ```
  python manage.py zip_archive 1 --settings=arch.settings
  ```

- To create a zipped archive for all archive groups.

  ```
  python manage.py zip_album --all --settings=arch.settings
  ```
  
- the zipped archive will be saved in the `media` directory. It can be donwloaded via the link [/media/archive_[archive.id]/archive_[archive.name].zip]()


## Create Translations

**Note:** _This requires to install GNU gettext tools e.g. via_ `sudo apt-get install gettext`

#### 1. Create message file

```
django-admin makemessages --ignore="static" --ignore=".env"  -l de
```

#### 2. Add translations to `.po` file.

#### 3. compile message file

```
django-admin compilemessages
```

## Create a graph representation of the data model

**Note**: _These instructions are for Ubuntu OS._ 

#### 1. Install Requirements

Requires Graphviz and PyGraphviz or pyparsing and pydot

```
sudo apt-get install graphviz graphviz-dev
pip install pygraphviz
```
Or
```
pip install pyparsing pydot
```

#### 2. Generate PNG file.

```
python arch/manage.py graph_models arch_app -g -o data_model.png
```

#### 3. create .dot file:

```
python arch/manage.py graph_models arch_app > data_model.dot
```

see docs here: https://django-extensions.readthedocs.io/en/latest/graph_models.html
