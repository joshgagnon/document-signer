import "babel-polyfill";
import * as React from "react";
import * as ReactDOM from "react-dom";
import { Provider, connect } from 'react-redux';
import { Store, createStore } from 'redux';
import configureStore from './configureStore';
import { addDocument, updateDocument, submitDocuments, removeDocument, updateForm } from './actions';
import App from './components/app';
import routes from './routes';
import { Router } from 'react-router';
import { History } from 'history';

import '../style/style.scss';

const ConnectedApp = connect(state => ({documents: state.documents, form: state.form}), {
    addDocument: addDocument,
    updateDocument: updateDocument,
    submitDocuments: submitDocuments,
    removeDocument: removeDocument,
    updateForm: updateForm
})(App);

interface RootProps {
    history: History,
    store: any
}

export default class Root extends React.Component<RootProps, {}> {
    render() {
        return (
            <Provider store={this.props.store}>
                <Router history={this.props.history}>
                    { routes(ConnectedApp) }
                    { this.props.children }
                </Router>
            </Provider>
        );
    }
}