import Vue from 'vue/dist/vue';
import VueVisible from '../src/v-visible.js';

Vue.use(VueVisible);

describe('visibility', () => {
    it ('should be visible', done => {
        const vm = new Vue({
            data: {
                visible: false
            },

            mounted() {
                setTimeout(_ => {
                    this.visible = true;

                    this.$nextTick(next);
                }, 3000);
            },

            template: `<div>
                <div class="content" v-visible="visible">Content</div>
            </div>`
        }).$mount();

        expect(vm.$el.querySelector('div .content').style.visibility).toBe('hidden');

        function next () {
            expect(vm.$el.querySelector('div .content').style.visibility).toBe('visible');
            done();
        }
    });
});
