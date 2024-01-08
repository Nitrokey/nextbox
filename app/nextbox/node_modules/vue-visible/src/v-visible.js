const vVisible = {
    install(Vue) {
        Vue.directive('visible', (el, binding) => {
            var value = binding.value;

            if (!!value) {
                el.style.visibility = 'visible';
            } else {
                el.style.visibility = 'hidden';
            }
        });
    }
};

if (window.Vue) {
    window.Vue.use(vVisible);
}

export default vVisible;