from django import forms

class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label='Select a CSV file',
        help_text='The CSV file should have the following columns: username, email, role, first_name, last_name, parent_username (optional)'
    ) 