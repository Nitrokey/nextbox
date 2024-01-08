import { po } from 'gettext-parser'

import { getGettextBuilder } from '../lib/gettext'

describe('gettext', () => {

    beforeEach(() => {
        jest.spyOn(console, 'warn')
    })

    afterEach(() => {
        console.warn.mockRestore()
    })

    it('falls back to the original string', () => {
        const gt = getGettextBuilder()
            .setLanguage('de')
            .build()

        const translation = gt.gettext('Settings')

        expect(translation).toEqual('Settings')
    })

    it('does not log in production', () => {
        const gt = getGettextBuilder()
            .setLanguage('de')
            .build()

        gt.gettext('Settings')

        expect(console.warn).not.toHaveBeenCalled()
    })

    it('has optional debug logs', () => {
        const gt = getGettextBuilder()
            .setLanguage('de')
            .enableDebugMode()
            .build()

        gt.gettext('Settings')

        expect(console.warn).toHaveBeenCalled()
    })

    it('falls back to the original singular string', () => {
        const gt = getGettextBuilder()
            .setLanguage('en')
            .build()

        const translated = gt.ngettext('%n Setting', '%n Settings', 1)

        expect(translated).toEqual('1 Setting')
    })

    it('falls back to the original plural string', () => {
        const gt = getGettextBuilder()
            .setLanguage('en')
            .build()

        const translated = gt.ngettext('%n Setting', '%n Settings', 2)

        expect(translated).toEqual('2 Settings')
    })

    it('detects en as default locale/language', () => {
        const detected = getGettextBuilder()
            .detectLocale()
            .build()

        const manual = getGettextBuilder()
            .setLanguage('en')
            .build()

        expect(detected).toEqual(manual)
    })

    it('used nextcloud-style placeholder replacement', () => {
        const gt = getGettextBuilder()
            .setLanguage('de')
            .build()

        const translation = gt.gettext('I wish Nextcloud were written in {lang}', {
            lang: 'Rust'
        })

        expect(translation).toEqual('I wish Nextcloud were written in Rust')
    })

    it('used nextcloud-style placeholder replacement for plurals', () => {
        const gt = getGettextBuilder()
            .setLanguage('de')
            .build()

        const translation = gt.ngettext('%n {what} Setting', '%n {what} Settings', 2, {
            what: 'test',
        })

        expect(translation).toEqual('2 test Settings')
    })

    it('translates', () => {
        const pot = `msgid ""
msgstr ""
"Last-Translator: Translator, 2020\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Language: sv\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\n"

msgid "abc"
msgstr "def"
`
        const gt = getGettextBuilder()
            .setLanguage('sv')
            .addTranslation('sv', po.parse(pot))
            .build()

        const translation = gt.gettext('abc')

        expect(translation).toEqual('def')
    })

    it('translates plurals', () => {
        // From https://www.gnu.org/software/gettext/manual/html_node/Translating-plural-forms.html
        const pot = `msgid ""
msgstr ""
"Last-Translator: Translator, 2020\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Language: sv\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\n"

msgid "One file removed"
msgid_plural "%d files removed"
msgstr[0] "%n slika uklonjenih"
msgstr[1] "%n slika uklonjenih"
msgstr[2] "%n slika uklonjenih"
`
        const gt = getGettextBuilder()
            .setLanguage('sv')
            .addTranslation('sv', po.parse(pot))
            .build()

        const translation = gt.ngettext('One file removed', '%n files removed', 2)

        expect(translation).toEqual('2 slika uklonjenih')
    })

    it('does not escape special chars', () => {
        const gt = getGettextBuilder()
            .setLanguage('de')
            .build()

        const translation = gt.gettext('test & stuff')

        expect(translation).toEqual('test & stuff')
    })

})
