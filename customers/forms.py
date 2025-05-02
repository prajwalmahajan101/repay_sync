from django import forms

class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Please upload a CSV file containing customer data.'
    ) 