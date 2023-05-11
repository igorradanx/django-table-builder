import json
from django.http import HttpResponse, JsonResponse
from django.db import models, connection
from django.views import View
from django.apps import apps

def get_model_field(field_type):
    if field_type == 'string':
        return models.CharField(max_length=255)
    
    if field_type == 'number':
        return models.FloatField()
    
    if field_type == 'boolean':
        return models.BooleanField()
    
    raise ValueError(f"Invalid field type {field_type}")

class TableCreateView(View):
    def post(self, request):
        table_desc = json.loads(request.body)
        table_name = table_desc['name']

        # Define a dictionary to hold the field definitions for the Django model
        fields = {'__module__': __name__}
        for field_desc in table_desc['fields']:
            field_name = field_desc['name']
            field_type = field_desc['type']
            fields[field_name] = get_model_field(field_type)

        # Define the Django model class dynamically using the type() function
        model_class = type(table_desc['name'], (models.Model,), fields)

        # Create the database table using the model's schema
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(model_class)

        self.register_model(table_name, model_class)

        return JsonResponse({"success": True, "message": f"Table {table_name} created"})

    def register_model(self, name: str, model_class: models.Model):
        app_config = apps.get_app_config('table')
        app_config.models[name] = model_class

class TableUpdateView(View):
    def put(self, request, table_name):
        table_desc = json.loads(request.body)
        try:
            model = apps.get_model(app_label='table', model_name=table_name)
        except LookupError:
            return JsonResponse({"success": False, "message": f"Table {table_name} does not exist"})
        existing_fields = {field.name: field for field in model._meta.fields}

        with connection.schema_editor() as schema_editor:
            # Alter field type or add new field
            for field in table_desc['fields']:
                field_name = field['name']
                existing_field = existing_fields.pop(field_name, None)
                new_field = get_model_field(field['type'])
                new_field.column = field_name

                if existing_field:
                    # If the field already exists, check if the type needs to be changed
                    if type(existing_field) != type(new_field):
                        schema_editor.alter_field(model, model._meta.get_field(field_name), new_field)
                else:
                    # If the field doesn't exist, add it to the model
                    schema_editor.add_field(model, new_field)

            # Delete remaining fields in existing_fields
            for field_name in existing_fields:
                schema_editor.remove_field(model, existing_fields[field_name])

        return JsonResponse({"success": True, "message": f"Table {table_name} updated"})
        
class TableRowCreateView(View):
    def post(self, request, table_name):
        values = json.loads(request.body)
        
        try:
            model_class = apps.get_model(app_label='table', model_name=table_name)
        except LookupError:
            return JsonResponse({"success": False, "message": f"Table {table_name} does not exist"})
        
        instance = model_class()
        for field_name, value in values.items():
            setattr(instance, field_name, value)
        instance.save()
        
        return JsonResponse({"success": True, "message": f"Added a row to table {table_name}"})
    
class TableRowListView(View):
    def get(self, request, table_name):
        try:
            model_class = apps.get_model(app_label='table', model_name=table_name)
        except LookupError:
            return JsonResponse({"success": False, "message": f"Table {table_name} does not exist"})
        
        rows = list(model_class.objects.values())

        return JsonResponse(rows, safe=False)


