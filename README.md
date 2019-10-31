# dompare
A command line tool to diff two directories recursively.

## Demo:
![Demo](images/dompare-demo.svg)

Then  visit http://localhost:5140/xxx.html, as shown in output, you will see the detailed difference of these two directories:

![Diff Results](images/dompare-screenshot.png)


## Features
 1. Easy to use
 2. Recursively compare same name files in two directories.

## Installation
```bash
pip3 install dompare
```

## Using dompare
```bash
dompare folder-a folder-b
```
Then open your webbrowser and visit `http://localhost:5140`, you will see the difference information of `folder-a` and `folder-b`.

You can also use `--host` and `--port` options to change your host and port to listen:
```bash
dompare folder-a folder-b --host 0.0.0.0 --port 8888
```


## Contributing
Any contribution is welcomed. If you find a bug or have any new features, please create an issue or a pull request. 

## License
[MIT](LICENSE)
