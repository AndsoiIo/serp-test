### Requirements
- Python => 3.6
- aiohttp => 3.6.2

### Usage example
The script collects hints in the search bar of the *target* site using all combinations of three letters ("a" ... "яяя").
By default, on restart, parsing will start from the last request.

Running in debug mode
```bash
python -m main -d
```
Start scraping from the beginning
```bash
python -m main -o
```
Run with a config file
```bash
python -m main -c config.ini
python -m main --config config.ini
```

Writing to the specified database
```bash
python -m main -db custom.db
python -m main --database custom.db
```
Run with proxy (proxy is not supported at the moment)
```bash
python -m main -p 123.123.123.123:1234 223.223.223.223:2234
```