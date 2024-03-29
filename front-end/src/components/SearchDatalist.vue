<template>
    <section>
        <div class='is-search-datalist-items'>
            <ul>
                <li v-for='(selection, index) in selections' :key='index' @click='remove(index)'>
                    <slot name='items' v-bind:item='selection'>
                        {{ selection }}
                    </slot>
                </li>
            </ul>
        </div>
        <div class='is-component is-search-datalist'>
            <div class='is-icon is-search-datalist' v-on:click='focus()'></div>
            <input class='is-field is-search-datalist' type='text' ref='input' v-model='entry' @click="showForcedSuggestions()" @focus='showStrictSuggestions()' @blur='hideSuggestions()' @keydown.down='next()' @keydown.up='previous()' @keydown.esc='hideSuggestions()' @keydown.enter='enter()' />
        </div>
        <div class='is-search-datalist-suggestions' v-if='canShowSuggestions'>
            <ul ref="suggestionBox">
                <li class='noresult' v-show='suggestions.length === 0'>
                    <slot name='nosuggestion' v-bind:value='entry'>
                        No result for "{{ entry }}"
                    </slot>
                </li>
                <li v-for='(suggestion, index) in suggestions' :key='index' @mousedown='add(index)' @mouseenter='select(index)' @mouseleave='unselect()' ref='suggestions'>
                    <slot name='suggestions' v-bind:suggestion='suggestion'>
                        {{ suggestion }}
                    </slot>
                </li>
            </ul>
        </div>
    </section>
</template>

<script>
    import generics from './../lib/Generics';
    import debounce from 'debounce';
    import { Component } from '../lib/Enums.js';

    export default {
        name : 'search-datalist',
        mixins : [generics],

        props : {
            // id : specify an id (or a name) to identificate the component instance
            'id' : {
                type : [Number, String],
                default : undefined
            },

            // realtime : it defines if the Store object is updated for each change of the input
            'realtime' : {
                type : Boolean,
                default : false
            },

            // timeout : independant of realtime, duration between two requests (in ms) for suggestion query
            'timeout' : {
                type : Number,
                default : 300
            },
            
            // fields on which the search is done
            'field' : {
                type : [String, Array]
            },

            // fields on which the autcomplete box is filled up
            'suggestion' : {
                type : [String, Array]
            },

            // ES function used for item search
            'function' : {
                type : String,
                default : 'match'
            },

            // itemOperator : logical operator applied between each item
            'itemOperator' : {
                type : String,
                default : 'OR'
            },

            // propertyOperator : logical operator applied for each property of a specific item
            'propertyOperator' : {
                type : String,
                default : 'OR'
            },

            // suggestionOperator : logical operator applied for suggestions
            'suggestionOperator' : {
                type : String,
                default : 'OR'
            },

            // size : count of elements to show in the box
            'size' : {
                type : Number,
                default : 10
            },

            // placeholder : text which appears into the input
            'placeholder' : {
                type : String,
                default : 'Search'
            }
        },

        data : function() {
            return {
                CID : undefined,
                entry : '', // input value
                mutableField : this.field, // editable fields param
                mutableSuggestion : this.suggestion, // editable suggestion fields param
                itemFun : undefined, // function applied for items
                propertyFun : undefined, // function applied for propertie(s) of an item
                suggestionFun : undefined, // function applied for suggestion search
                localInstructions : [], // local request
                canShowSuggestions : false, // show suggestions list
                selections : [], // selected items
                suggestions : [], // suggestions list
                highlightedSuggestion : undefined, // current selected suggestion

                name : null,
                authorization : {
                    mount : true,
                    fetch : true
                },
                tagFilters : []
            };
        },

        computed : {
            computedEntry : function() {
                return this.entry.toLowerCase();
            },

            computedSelections : function() {
                return this.selections;
            }
        },

        watch : {
            computedEntry : function(value) {
                if (value.trim() !== '')
                    this.updateItems(value);
                else
                    this.hideSuggestions();
            },

            computedSelections : function(selections) {
 				// Reset all deep instructions of local request
                this.removeInstructions();
                
                // Case where the selection array is not empty : we add instructions
                if (selections.length > 0) {
                    // Local request data initialization for each field selection
                    let _instruction = {
                        fun : 'filter',
                        args : ['bool', arg => {
                            this.selections.forEach(selection => {
                                arg[this.itemFun]('bool', sub => {
                                    this.mutableField.forEach(attr => {
                                        sub[this.propertyFun](this.function, attr, selection._source[attr].toLowerCase());
                                    });

                                    return sub;
                                })
                            });

                            return arg;
                        }]
                    };

                    this.localInstructions.push(_instruction);
					this.addInstruction(_instruction);
                }

                // Send the value to TagFilter component(s)
                this.tagFilters.forEach(tagFilter => {
                    this.bus.$emit(tagFilter, this.selections);
                });

                // Update the request
                if (this.authorization.mount)
                    this.mount();
                else
                    this.authorization.mount = !this.authorization.mount; // consume the exception
            }
        },

        methods : {
            // Execute the mixins Fetch method to update hits
            executeSearch : function() {
                if (this.authorization.fetch)
                    this.fetch();
                else
                    this.authorization.fetch = !this.authorization.fetch; // consume the exception
            },

            // Focus on input
            focus : function() {
                this.$nextTick(function () {
                    this.$refs.input.focus();
                });
            },

            // Triggered when the input changes
            updateItems : function(value) {
                // Update suggestions
                let _suggsRequest = this.createRequestForSuggs(value, this.mutableSuggestion, this.selections, this.suggestionFun, this.size);
                this.header.client.search(_suggsRequest).then(response => {
                    // Reset suggestions
                    this.suggestions = [];

                    this.suggestions = response.hits.hits;

                    // Show the box
                    this.showStrictSuggestions();
                });
            },

            // Show the autosuggestion box
            showForcedSuggestions : function() {
                // Update suggestions
                let _suggsRequest = this.createRequestForSuggs(this.entry, this.mutableSuggestion, this.selections, this.suggestionFun, this.size);
                this.header.client.search(_suggsRequest).then(response => {
                    // Reset suggestions
                    this.suggestions = [];

                    this.suggestions = response.hits.hits;

                    // Show the box
                    this.canShowSuggestions = true;
                });
            },

            // Show the autosuggestion box when the entry is not empty
            showStrictSuggestions : function() {
                if (this.entry.trim() !== '')
                    this.canShowSuggestions = true;
            },

            // Hide the autosuggestion box
            hideSuggestions : function() {
                // Stop any debounced request only for searchdatalist components
                this.resetDebounce('searchdatalist');

                this.canShowSuggestions = false;
                this.unselect();
            },

            // Add a suggested item
            add : function(index) {
                this.selections.push(this.suggestions[index]);
                this.entry = '';
                this.hideSuggestions();
                this.focus();
            },

            // Remove a suggested item
            remove : function(index) {
                this.selections.splice(index, 1);
                this.focus();
            },

            // Select (highlight) a suggested item
            select : function(index) {
                let _el = this.$refs.suggestions[index];
                if (_el !== undefined) {
                    if (this.highlightedSuggestion !== undefined)
                        this.unselect();

                    this.highlightedSuggestion = index;
                    _el.classList.add('selected');
                }
            },

            // Unselect a suggested item
            unselect : function() {
                let _index = this.highlightedSuggestion,
                    _el = this.$refs.suggestions;
                if (_el !== undefined && _el[_index] !== undefined) {
                    this.highlightedSuggestion = undefined;
                    _el[_index].classList.remove('selected');
                }
            },

            // Select the next suggestion from highlighted item
            next : function() {
                let _index = this.highlightedSuggestion;
                if (_index === undefined)
                    this.selectAndScroll(0);
                else
                    this.selectAndScroll((_index + 1) % this.suggestions.length);
            },

            // Select the previous suggestion from highlighted item
            previous : function() {
                let _index = this.highlightedSuggestion,
                    _size = this.suggestions.length;
                if (_index === undefined)
                    this.selectAndScroll(_size - 1)
                else
                    this.selectAndScroll((((_index - 1) % _size) + _size) % _size)
            },

            // When 'enter' is pushed, add the highlighted item to the selections array
            enter : function() {
                if (this.canShowSuggestions) {
                    // If an item is selected
                    let _index = this.highlightedSuggestion;
                    if (_index !== undefined && this.$refs.suggestions[_index] !== undefined)
                        this.add(_index);

                    this.hideSuggestions();
                }
            },
            
            // Scroll function
            selectAndScroll : function(index) {
                let _refSugg = this.$refs.suggestions[index];
                if (_refSugg !== undefined) {
                   let  _itemHeight = _refSugg.offsetHeight;
                    this.select(index);
                    this.$refs.suggestionBox.scrollTo(0, index * _itemHeight);
                }
            },

            // Set authorizations of mount and fetch methods to false (for reset behavior)
            setAuthorizations : function() {
                this.authorization.mount = false;
                this.authorization.fetch = false;
            },

            // Reset items and input
            reset : function() {
                this.setAuthorizations();
                this.entry = '';
                this.selections = [];
            }
        },

        mounted : function() {
            // Add placeholder property to the input html tag
            this.$refs.input.setAttribute('placeholder', this.placeholder);
        },

        created : function() {
			// Interactive component declaration
            this.CID = this.addComponent(Component.SEARCH_DATALIST, this);

            // Assign the name to the component if needed
            if (this.id !== undefined)
                this.name = this.id;

            // Create a dynamic watcher on the input which calls the mixins Fetch function
            let _disableWatcherFetch = this.$watch(function() {
                return this.selections;
            }, {
                handler : function(val) {
                    this.executeSearch.call(this);
                },
                deep : true
            });

            // Behavior when realtime is disabled
            if (!this.realtime)
                _disableWatcherFetch(); // Disable the watcher that disable fetch event
            
            // Debounce for suggestion list update
            let _debounce = debounce(this.updateItems, this.timeout); // Debounce method with the timeout value on the current SeachOn function
            this.addDebounce(Component.SEARCH_DATALIST, _debounce); // Add debounce event to listed debounce into the Store
            this.updateItems = _debounce; // Apply debounce

            // Convert field string to field array
            if (!Array.isArray(this.mutableField))
                this.mutableField = [this.mutableField];

            // Convert suggestion string to suggestion array
            if (!Array.isArray(this.mutableSuggestion))
                this.mutableSuggestion = [this.mutableSuggestion];

            // Functions calculation depending on operator
            this.itemFun = (this.itemOperator.toUpperCase() === 'AND') ? 'filter' : 'orFilter';
            this.propertyFun = (this.propertyOperator.toUpperCase() === 'AND') ? 'filter' : 'orFilter';
            this.suggestionFun = (this.suggestionOperator.toUpperCase() === 'AND') ? 'filter' : 'orFilter';

            // Triggered by ResetButton and TagFilter components
            this.bus.$on('reset', () => this.reset());
            this.bus.$on('reset_' + this.CID, () => { this.reset(); this.focus(); });
            this.bus.$on('resetByValue_' + this.CID, (value) => {
                this.remove(value);
                this.focus();
            });

            // Save TagFilter channel(s)
            this.bus.$on('tagFilter_' + this.CID, (channel) => {
                this.tagFilters.push(channel);
            });
        }
    };
</script>
