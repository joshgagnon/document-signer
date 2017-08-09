import  * as React from "react";
import { ResultsModal } from './results';
import { SignatureModal, InitialsModal } from './signatureSelector';
import { connect } from 'react-redux';
import { closeShowingModal } from '../actions/index';

class Modals extends React.PureComponent<any>{
    render() {
        switch(this.props.showing){
            case 'selectSignature':
                return <SignatureModal hideModal={this.props.closeShowingModal} />;
            case 'results':
                return <ResultsModal hideModal={this.props.closeShowingModal} />;
            case 'selectInitial':
                return <InitialsModal hideModal={this.props.closeModal} />
            default:
                return false;
        }
    }
}


export default connect(
    (state: Sign.State) => ({
        showing: state.modals.showing
    }),
    {
        closeShowingModal: closeShowingModal,
    }
)(Modals)
