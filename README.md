# transaction-organizer
A personal project project to build an app to help me organize my transactions

## API Reference

```
/transactions
    GET:            3 latest transactions
    POST:           Add a new transaction
    /<id>
        GET:        View the transaction by id
        POST:       Update the transaction by id
        DELETE:     Delete the transaction by id
        /delete
            POST:   HTML form-friendly version of delete request

/tables
    GET:            View a table of all transactions
    /download   
        GET:        Download all transactions as either a .csv or .xslx file
    /pivot
        GET:        View the pivot table
        /download:
            GET:    Download the pivot table data as either a .csv or .xslx file

/autocomplete
    GET:            Autocomplete the given query
```
