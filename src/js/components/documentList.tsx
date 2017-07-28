import * as React from 'react';
import * as ReactCSSTransitionGroup from 'react-addons-css-transition-group';
import PDFThumbnail from './pdf/thumbnail';
import PDFPage from './pdf/page';

interface DocumentViewProps {
    document: Sign.Document;
    removeDocument: Function;
}

interface DocumentListProps {
    documents: Sign.Document[];
    removeDocument: Function;
    getPDF: Function;
};

const A4_RATIO = 1.414;

const THUMBNAIL_WIDTH = 150;
const THUMBNAIL_HEIGHT = THUMBNAIL_WIDTH * A4_RATIO;

const DocumentView = (props: DocumentViewProps) => (
    <div className="document">
        <button className="remove" onClick={() => props.removeDocument()}>✖</button>

        <PDFPage pageNumber={1} drawWidth={THUMBNAIL_WIDTH} docId={props.document.id} />
        <div className="filename">{ props.document.filename }</div>
        
        <ReactCSSTransitionGroup transitionName="progress" transitionEnterTimeout={300} transitionLeaveTimeout={300}>
            { props.document.uploadStatus === Sign.DocumentUploadStatus.InProgress &&
                <div className="progress" key="progress">
                    <div className="progress-bar progress-bar-striped active" style={{width: `${props.document.progress*100}%`}}></div>
                </div>
            }
        </ReactCSSTransitionGroup>
    </div>
);

export default class DocumentList extends React.Component<DocumentListProps> {
    render() {
        return (
            <div className="document-list clearfix">
                {this.props.documents.map(doc => <DocumentView key={doc.id} document={doc} removeDocument={() => {this.props.removeDocument(doc.id)}} />)}
            </div>
        );
    }
}