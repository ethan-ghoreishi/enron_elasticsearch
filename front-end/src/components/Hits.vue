<template>
    <section v-if="hits.score != undefined" class="is-component is-hits">
        <slot name="hits" v-bind:hits="hits">
            <div class="is-score is-hits">
                <strong v-if="hits.score === 0">No result found</strong>
                <strong v-else-if="hits.score === 1">1 result found</strong>
                <strong v-else-if="hits.score > 1">{{ hits.score }} results found</strong>
            </div>
            <div v-for="(item, index) in hits.items" :key="index" :item="item">
                <div>{{ item }}</div>
            </div>
        </slot>
    </section>
</template>

<script>
    import generics from './../lib/Generics';
    import { Component } from '../lib/Enums.js';

    export default {
        name : "hits",
        mixins : [generics],

        data : function() {
            return {
                CID : undefined
            }
        },

        computed : {
            hits : function() {
                return {
                    items : this.items,
                    score : this.score
                };
            }
        },

        methods : {
            emptyHits : function() {
                this.clearItems();
                this.setScore(undefined);
            }
        },

        created : function() {
            // Interactive component declaration
            this.CID = this.addComponent(Component.HITS, this);

            this.bus.$on('emptyHits', () => {
                this.emptyHits();
            });
        }
    };
</script>
