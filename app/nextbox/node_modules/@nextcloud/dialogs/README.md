# @nextcloud/dialogs

Nextcloud dialog helpers

## Installation

```
npm i -S @nextcloud/dialogs
```

## Usage

### Toasts

```js
import { showMessage, showInfo, showSuccess, showWarning, showError } from '@nextcloud/dialogs'
import '@nextcloud/dialogs/styles/toast.scss'
```

Make sure that the  `@nextcloud/dialogs/styles/toast.scss` file is included in your app to make sure that the toasts have a proper styling applied.

There are different toast styles available, that are exposed in separate functions:

```
showMessage('Message without a specific styling')
showInfo('Information')
showSuccess('Success')
showWarning('Warning')
showError('Error')
```

There are several options that can be passed in as a second parameter, like the timeout of a toast:

```
showError('This is an error shown without a timeout', { timeout: -1 })
```

A full list of available options can be found in the [documentation](https://nextcloud.github.io/nextcloud-dialogs/).

## Releasing a new version

- Checkout latest master (pull);
- Edit CHANGELOG.md and add new entries there for the new version, then create a commit;
- Run `npm version patch` (`npm version minor` if minor). This will return a new version name, make sure it matches what was added in the CHANGELOG.md;
- Push the tag and the master branch `git push origin master [printed-version-name]`;
- Make the tag a release on github and add the changelog (https://github.com/nextcloud/nextcloud-dialogs/releases);
- Click edit on a previous release and copy the body of the changelog;
- Go back, click on your release and paste the copied text;
- Edit all the version numbers;
- Click on preview and click on view full changelog, this will show you all the prs that have been; added since the previous version;
- Copy them in the changelog with the same format as previous ones;
