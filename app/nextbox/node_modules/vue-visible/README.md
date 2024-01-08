# VueVisible

v-visible directive for VueJS (2.x)

## Demo
A jsFiddle live demo: https://jsfiddle.net/fcpc6utm/

## About

This plugins adds a v-visible directive (similar to the native v-show) that changes the `visibility` style of the applied element (hidden or visible).

## Install

With npm:

```
npm install --save vue-visible
```

## Usage

If you're using modules, first import it:

```
import VueVisible from 'vue-visible';

Vue.use(VueVisible);
```

Then in your template just use the directive:

```
<div v-visible="myCondition">I'm visible</div>
```

Or if you're not using modules, just include the js:

```
<script src="node_modules/vue-visible/dist/v-visible.js"></script>
```
```
<div v-visible="myCondition">I'm visible</div>
```
