SMA and RSI Forward Tester
This repository contains a Python-based trading bot that uses Simple Moving Averages (SMA) and Relative Strength Index (RSI) for forward testing various trading strategies on cryptocurrency pairs.
The bot fetches market data, calculates technical indicators, and simulates trades to find the best parameters for maximizing returns.

Table of Contents:

Installation
Usage
Project Structure
Configuration
Contributing
License
Installation
Clone the repository:

Create a virtual environment:

Install the required dependencies:

Usage
Run the forward tester:

Check the results:

The results will be printed in the console, showing the best parameters and the performance metrics.

Project Structure
Key Files
Packages/Tester/SMA_RSI_ForwardTester.py: Main script for forward testing SMA and RSI strategies.
MarketData: Contains scripts and data for fetching market data.
Logs: Directory for storing log files.
requirements.txt: List of dependencies required for the project.
Configuration
You can configure the parameters for the forward tester in the SMA_RSI_ForwardTester.py script:

Contributing
Contributions are welcome! Please follow these steps to contribute:

Fork the repository.
Create a new branch (git checkout -b feature-branch).
Make your changes.
Commit your changes (git commit -am 'Add new feature').
Push to the branch (git push origin feature-branch).
Create a new Pull Request.
License
This project is licensed under the MIT License. See the LICENSE file for details.
