new Vue({
    el: '#app',

    created() {
        for (let i=0, l=Math.round(Math.random() * 10); i<l; i++) {
            this.cards.push({
                visible: true,
                type: ['show', 'visible'][i % 2]
            });
        }
    },

    data: {
        cards: []
    },

    methods: {
        toggle(card) {
            card.visible = !card.visible;
        }
    },

    template: `<div>
        <div class="card" v-for="card in cards">
            <div class="content" v-if="card.type === 'show'" v-show="card.visible">This is with v-show</div>
            <div class="content" v-if="card.type === 'visible'" v-visible="card.visible">This is with v-visible</div>
            <span class="btn btn-primary" @click="toggle(card)">Toggle</span>
        </div>
    </div>`
});