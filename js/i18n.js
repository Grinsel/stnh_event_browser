/**
 * Internationalisation / language switching module.
 */
const I18n = (() => {
    let currentLang = 'english';
    let locData = {};

    async function setLanguage(lang) {
        currentLang = lang;
        locData = await DataManager.loadLocalisation(lang);
        return locData;
    }

    function t(key) {
        if (!key) return '';
        return locData[key] || key;
    }

    function getLang() { return currentLang; }
    function getData() { return locData; }

    return { setLanguage, t, getLang, getData };
})();
