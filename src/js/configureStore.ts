import { createStore, applyMiddleware, compose} from 'redux';
import rootReducer from './reducers';
import * as thunk from 'redux-thunk';
import { routerMiddleware } from 'react-router-redux';
import { createLogger } from 'redux-logger';

import createSagaMiddleware from 'redux-saga';
import rootSaga from './sagas';


// using any for history due to changes in ts definition
export default function configureStore(history :any, initialState={}) {
const loggerMiddleware = createLogger();
const sagaMiddleware = createSagaMiddleware();


    const middleware =  DEV ?  applyMiddleware(
        sagaMiddleware,
        <any>thunk.default,
        loggerMiddleware,
        routerMiddleware(history)
    ) : applyMiddleware(
        sagaMiddleware,
        <any>thunk.default,
        loggerMiddleware,
        routerMiddleware(history)
    )

    const createStoreWithMiddleware = compose(middleware)(createStore);
    const store = createStoreWithMiddleware(rootReducer, initialState);

    sagaMiddleware.run(rootSaga);

    return store;
}
