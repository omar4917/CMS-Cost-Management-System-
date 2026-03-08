import { createContext, useContext, useState, useEffect } from 'react';
import { currencyAPI } from '../services/api';

const CurrencyContext = createContext(null);

export const useCurrency = () => useContext(CurrencyContext);

export function CurrencyProvider({ children }) {
    const [currencies, setCurrencies] = useState([]);
    const [selectedCurrency, setSelectedCurrency] = useState(
        localStorage.getItem('cms_currency') || 'BDT'
    );
    const [rates, setRates] = useState({});
    const [baseCurrency, setBaseCurrency] = useState('BDT');

    useEffect(() => {
        loadCurrencies();
    }, []);

    const loadCurrencies = async () => {
        try {
            const res = await currencyAPI.getAll();
            const currencyList = res.data.currencies;
            setCurrencies(currencyList);

            const rateMap = {};
            currencyList.forEach(c => {
                rateMap[c.code] = parseFloat(c.exchangeRateToBase);
                if (c.isBase) setBaseCurrency(c.code);
            });
            setRates(rateMap);
        } catch (error) {
            // Fallback rates
            setRates({ BDT: 1, USD: 0.0084, EUR: 0.0077, GBP: 0.0066 });
        }
    };

    const changeCurrency = (code) => {
        localStorage.setItem('cms_currency', code);
        setSelectedCurrency(code);
        // Page reload for full recalculation as requested by user
        window.location.reload();
    };

    const convert = (amount, fromCurrency = baseCurrency) => {
        if (!amount || isNaN(amount)) return 0;
        const amt = parseFloat(amount);
        if (fromCurrency === selectedCurrency) return amt;

        // Convert to base currency first, then to target
        const fromRate = rates[fromCurrency] || 1;
        const toRate = rates[selectedCurrency] || 1;
        const baseAmount = amt / fromRate;
        return baseAmount * toRate;
    };

    const format = (amount, fromCurrency = baseCurrency) => {
        const converted = convert(amount, fromCurrency);
        const curr = currencies.find(c => c.code === selectedCurrency);
        const symbol = curr?.symbol || selectedCurrency;

        return `${symbol} ${converted.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        })}`;
    };

    return (
        <CurrencyContext.Provider value={{
            currencies, selectedCurrency, baseCurrency, rates,
            changeCurrency, convert, format, loadCurrencies,
        }}>
            {children}
        </CurrencyContext.Provider>
    );
}
