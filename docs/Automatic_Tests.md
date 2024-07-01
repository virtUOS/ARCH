# create tests

Create a test by copying the template below into `arch/arch_app/tests/tests.py` and write the respective test cases as functions which starts with `test`:

```
class TemplateTests(TestCase, BaseSetup):
    """ Template test """
    def setUp(self):
        """ setup """
        self.setUpDB()

    def test_base_template(self):
        """ test """
        self.assertIs(True, True)
```


# run tests

run the tests with the following command:

```python manage.py test arch_app.tests```
