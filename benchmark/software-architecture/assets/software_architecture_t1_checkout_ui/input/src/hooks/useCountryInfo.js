import { useContext, useEffect, useState } from 'react';
import { CheckoutStore } from '../store';

const useCountryInfo = (address) => {
  const { state } = useContext(CheckoutStore);
  const countryInfo = state.initialData.country_info;

  const [currentCountryInfo, setCurrentCountryInfo] = useState({
    countries: [],
    provinces: [],
    showPostalCode: false,
    showProvince: false,
    provinceLabel: 'Province',
  });

  useEffect(() => {
    if (countryInfo) {
      const unsortedCountries = Object.values(countryInfo);
      // eslint-disable-next-line no-nested-ternary
      const countries = unsortedCountries.sort((a, b) => ((a.name > b.name) ? 1 : ((b.name > a.name) ? -1 : 0)));
      let provinces = [];
      let showPostalCode = false;
      let showProvince = false;
      let provinceLabel = 'Province';

      if (address?.country_code) {
        const countryData = countries.find((countryItem) => countryItem.iso_code === address.country_code);

        if (countryData) {
          // eslint-disable-next-line no-nested-ternary
          provinces = countryData.provinces.sort((a, b) => ((a.name > b.name) ? 1 : ((b.name > a.name) ? -1 : 0)));
          showPostalCode = countryData.show_postal_code;
          showProvince = countryData.show_province;
          provinceLabel = countryData.province_label;
        }
      }

      setCurrentCountryInfo({
        countries,
        provinces,
        showPostalCode,
        showProvince,
        provinceLabel,
      });
    }
  }, [countryInfo, address?.country_code]);

  return {
    data: {
      countries: currentCountryInfo.countries,
      provinces: currentCountryInfo.provinces,
      showProvince: currentCountryInfo.showProvince,
      showPostalCode: currentCountryInfo.showPostalCode,
      provinceLabel: currentCountryInfo.provinceLabel,
    },
  };
};

export default useCountryInfo;
