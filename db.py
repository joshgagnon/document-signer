"""

Functions for working with the database

"""

import psycopg2
import psycopg2.extras
from flask import g, current_app
import uuid
import json
from collections import defaultdict

def get_db():
    """
    Return a connected database instance and save it to flask globals for next time
    """
    if not hasattr(g, 'db') or g.db.closed:
        g.db = connect_db_config(current_app.config)
    return g.db


def close_db():
    """
    If we have saved a conencted database instance to flask globals, close the connection
    """
    if hasattr(g, 'db') and not g.db.closed:
        g.db.close()


def connect_db_config(config):
    """
    Create a psycopg2 connection to the database
    """
    connection = psycopg2.connect(
        database=config['DB_NAME'],
        user=config['DB_USER'],
        password=config['DB_PASS'],
        host=config['DB_HOST'])
    return connection


def add_signature(user_id, binary_file_data, signature_type):
    """
    Add a signature to the database
    """
    database = get_db()
    with database.cursor() as cursor:
        query = """
            INSERT INTO signatures (user_id, signature, type)
            VALUES (%(user_id)s, %(blob)s, %(signature_type)s)
            RETURNING signature_id
        """

        cursor.execute(query, {
            'user_id': user_id,
            'blob': psycopg2.Binary(binary_file_data),
            'signature_type': signature_type
        })
        database.commit()
        return cursor.fetchone()[0]


def find_or_create_and_validate_document_set(set_id, user_id):
    """
    Find or create a document set, making sure the user has permission to access it
    """
    database = get_db()
    with database.cursor() as cursor:
        find_doc_set_query = """
            SELECT user_id
            FROM document_sets
            WHERE document_set_id = %(set_id)s
        """
        cursor.execute(find_doc_set_query, {
            'set_id': set_id,
        })
        result = cursor.fetchone()

        if not result:
            try:
                create_doc_set_query = """
                    INSERT INTO document_sets (document_set_id, user_id)
                    VALUES (%(set_id)s, %(user_id)s)
                """

                cursor.execute(create_doc_set_query, {
                    'set_id': set_id,
                    'user_id': user_id
                })

                database.commit()
            except Exception as e:
                database.rollback()
                pass
        elif result[0] != user_id:
            raise Exception
        else:
            update_document_set = """
                UPDATE document_sets SET deleted_at = NULL
                WHERE document_set_id = %(set_id)s
            """
            cursor.execute(update_document_set, {
                'set_id': set_id,
            })
            database.commit()


def add_document(set_id, document_id, filename, binary_file_data, source='uploaded'):
    """
    Add a document to the database. If no UUID is passed, one will be created
    by the database.
    """
    database = get_db()
    if not document_id:
        document_id = str(uuid.uuid4())
    with database.cursor() as cursor:
        # Create the document data record
        create_doc_data_query = """
            INSERT INTO document_data (data)
            VALUES (%(blob)s)
            RETURNING document_data_id
        """

        cursor.execute(create_doc_data_query, {
            'blob': psycopg2.Binary(binary_file_data)
        })
        data_id = cursor.fetchone()[0]

        # Create the document record, including the ID of the document data
        create_document_query = """
            INSERT INTO documents (document_id, document_set_id, filename, document_data_id, source)
            VALUES (%(document_id)s, %(set_id)s, %(filename)s, %(document_data_id)s, %(source)s)
            RETURNING document_id
        """

        cursor.execute(create_document_query, {
            'document_id': document_id,
            'set_id': set_id,
            'filename': filename,
            'document_data_id': data_id,
            'source': source
        })
        document_id = cursor.fetchone()[0]

        database.commit()

        # Return the document ID and the filename
        return {
            'document_id': document_id,
            'filename': filename
        }

def add_document_set_meta(document_set_id, meta):
    database = get_db()

    with database.cursor() as cursor:
        cursor.execute("""
                       INSERT INTO document_meta (document_set_id, field_data) VALUES (%(document_set_id)s, %(field_data)s)
                       """, {
            'document_set_id': document_set_id,
            'field_data': psycopg2.extras.Json(meta)
        })
        database.commit()


def get_document_set_meta(document_set_id):
    database = get_db()

    with database.cursor() as cursor:
        cursor.execute("""
                       SELECT field_data FROM  document_meta WHERE document_set_id = %(document_set_id)s
                       """, {
            'document_set_id': document_set_id
        })
        try:
            return cursor.fetchone()[0]
        except:
            return None


def remove_document_from_set(user_id, document_id):
    database = get_db()
    with database.cursor() as cursor:
        # Create the document data record
        delete_query = """
            SELECT delete_document(%(user_id)s, %(document_id)s)
        """
        cursor.execute(delete_query, {'user_id': user_id, 'document_id': document_id})
        document_set_id = cursor.fetchone()[0]
        database.commit()



def get_signatures_for_user(user_id):
    """
    Get all signatures for a user
    """
    database = get_db()
    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        query = """
            SELECT signature_id, type
            FROM signatures
            WHERE user_id = %(user_id)s
                AND (type = 'signature' OR type = 'initial')
                AND deleted IS FALSE
        """
        cursor.execute(query, {'user_id': user_id})
        signatures = cursor.fetchall()
        database.commit()
        return [dict(x) for x in signatures]


def get_signature(signature_id, user_id):
    """
    Get a signature, making sure the user has permission to access it
    """
    database = get_db()
    with database.cursor() as cursor:
        query = """
            SELECT signature
            FROM signatures
            WHERE signature_id = %(signature_id)s
                AND user_id = %(user_id)s
        """
        cursor.execute(query, {
            'signature_id': signature_id,
            'user_id': user_id,
        })
        first_row = cursor.fetchone()
        database.commit()
        if first_row is None:
            return None

        return first_row[0]


def remove_signature(signature_id, user_id):
    """
    remove a signature, making sure the user has permission to access it
    """
    database = get_db()
    with database.cursor() as cursor:
        query = """
            UPDATE signatures SET deleted = true
            WHERE signature_id = %(signature_id)s
                AND user_id = %(user_id)s
                RETURNING signature_id
        """
        cursor.execute(query, {
            'signature_id': signature_id,
            'user_id': user_id,
        })
        result = cursor.fetchone()
        if result:
            result = result[0]
    database.commit()
    return result


def upsert_user(user):
    """
    Create or update a user
    """
    database = get_db()

    user_dict = defaultdict(lambda: False)
    user_dict.update(user)

    user = user_dict

    if current_app.config.get('USE_DB_UPSERT'):
        if user.get('subscribed', None) is not None:
            query = """
                INSERT INTO users (user_id, name, email, subscribed, email_verified)
                VALUES (%(user_id)s, %(name)s, %(email)s, %(subscribed)s, %(email_verified)s)
                ON CONFLICT (user_id) DO UPDATE SET name = %(name)s, email = %(email)s, subscribed = %(subscribed)s;
            """
        else:
            query = """
                INSERT INTO users (user_id, name, email)
                VALUES (%(user_id)s, %(name)s, %(email)s)
                ON CONFLICT (user_id) DO UPDATE SET name = %(name)s, email = %(email)s
            """
        with database.cursor() as cursor:
            cursor.execute(query, user)
        database.commit()
    else:
        try:
            if user.get('subscribed', None) is not None:
                query = """
                    INSERT INTO users (user_id, name, email, subscribed, email_verified)
                    VALUES (%(user_id)s, %(name)s, %(email)s, %(subscribed)s, %(email_verified)s)
                """
            else:
                query = """
                    INSERT INTO users (user_id, name, email)
                    VALUES (%(user_id)s, %(name)s, %(email)s)
                """
            with database.cursor() as cursor:
                cursor.execute(query, user)

        except:
            database.rollback()
            if user.get('subscribed', None) is not None:
                query = """
                    UPDATE users SET name = %(name)s, email = %(email)s, subscribed = %(subscribed)s, email_verified = %(email_verified)s where user_id = %(user_id)s;
                """
            else:
                query = """
                    UPDATE users SET name = %(name)s, email = %(email)s where user_id = %(user_id)s;
                """
            with database.cursor() as cursor:
                cursor.execute(query, user)
        database.commit()
    return


def get_user_info(user_id):
    """
    Get a user's basic info
    """
    database = get_db()
    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        query = """
            SELECT user_id, name, email, email_verified, subscribed from users where user_id = %(user_id)s
        """
        cursor.execute(query, {'user_id': user_id})
        result = dict(cursor.fetchone())
        database.commit()
        return result



def get_user_document_sets(user_id):
    """
    Get latest document sets for a user
    """
    database = get_db()
    query = """
        SELECT user_document_sets_json(%(user_id)s)
    """
    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, {'user_id': user_id})
        data = cursor.fetchall()
        result = [x[0] for x in data]
        database.commit()
        return result


def get_document(user_id, document_id):
    """
    Get a document, checking the user has permission to access it
    """
    database = get_db()
    query = """
        SELECT d.document_id, d.document_set_id, d.hash, d.filename, dd.data
        FROM documents d
        JOIN document_data dd on d.document_data_id = dd.document_data_id
        JOIN documents ddd on ddd.document_id = original_document_id(%(document_id)s)
        JOIN document_sets ds on ddd.document_set_id = ds.document_set_id
        LEFT OUTER JOIN sign_requests sr ON sr.document_id = ddd.document_id
        WHERE d.document_id = %(document_id)s AND (ds.user_id = %(user_id)s OR sr.user_id = %(user_id)s)
    """
    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, {
            'user_id': user_id,
            'document_id': document_id
        })
        first_row = cursor.fetchone()
        database.commit()
        if first_row is None:
            return None

        return first_row


def sign_document(user_id, input_document_id, result_document_id, sign_request_id, data):
    """
    Sign a document
    """
    database = get_db()
    insert = """
        INSERT INTO sign_results (user_id, input_document_id, result_document_id, sign_request_id, field_data)
        VALUES (%(user_id)s, %(input_document_id)s, %(result_document_id)s, %(sign_request_id)s, %(field_data)s)

    """
    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(insert, {
            'user_id': user_id,
            'input_document_id': input_document_id,
            'result_document_id': result_document_id,
            'sign_request_id': sign_request_id,
            'field_data': psycopg2.extras.Json(data)
        })
        database.commit()

def reject_document(user_id, input_document_id, sign_request_id, data):
    """
    Sign a document
    """
    database = get_db()
    insert = """
        INSERT INTO sign_results (user_id, input_document_id, result_document_id, sign_request_id, field_data, accepted)
        VALUES (%(user_id)s, %(input_document_id)s, null, %(sign_request_id)s, %(field_data)s, false)

    """
    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(insert, {
            'user_id': user_id,
            'input_document_id': input_document_id,
            'sign_request_id': sign_request_id,
            'field_data': psycopg2.extras.Json(data)
        })
        database.commit()

def get_document_set(user_id, set_id):
    """
    Get the info about a document set
    """
    database = get_db()
    query = """
    SELECT document_set_json(%(user_id)s, %(set_id)s)
    """
    with database.cursor() as cursor:
        cursor.execute(query, {
            'user_id': user_id,
            'set_id': set_id
        })
        data = cursor.fetchone()[0]
        database.commit()
        return data


def add_signature_requests(document_set_id, requests):
    database = get_db()
    query = b"""
        INSERT INTO sign_requests(document_id, user_id, field_data) VALUES
    """
    inserts = []
    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        for req in requests:
            for document_id in req.get('documentIds', []):
                inserts.append(cursor.mogrify("(%s, %s, %s)", (document_id, req['recipient']['user_id'], json.dumps([]))))
            if len(req.get('prompts', [])):
                # group by document id
                promptMap = defaultdict(list)
                for p in req.get('prompts'):
                    promptMap[p['documentId']] += [p]
                for document_id, prompts in promptMap.items():
                    inserts.append(cursor.mogrify("(%s, %s, %s)", (document_id, req['recipient']['user_id'], json.dumps(prompts))))
        cursor.execute(query + b', '.join(inserts))
        database.commit()


def revoke_signature_requests(user_id, sign_request_id):
    database = get_db()
    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        query = """
            SELECT revoke_signature_request(%(user_id)s, %(sign_request_id)s)
        """
        with database.cursor() as cursor:
            cursor.execute(query, {
                           'user_id': user_id,
                           'sign_request_id': sign_request_id
                           })
        database.commit()

def document_set_from_request_id(user_id, sign_request_id):
    database = get_db()
    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        query = """
            SELECT ds.document_set_id  as document_set_id
            FROM
            sign_requests sr
            JOIN documents d on sr.document_id = d.document_id
            JOIN document_sets ds on ds.document_set_id = d.document_set_id
            WHERE ds.user_id = %(user_id)s and sign_request_id = %(sign_request_id)s
        """
        cursor.execute(query, {
                       'user_id': user_id,
                       'sign_request_id': sign_request_id
                       })

        result = cursor.fetchone()
        database.commit()
        return result.get('document_set_id') if result else None


def save_document_view(document_id, user_id, field_data):
    database = get_db()
    args = {'document_id': document_id, 'field_data': psycopg2.extras.Json(field_data), 'user_id': user_id}
    if current_app.config.get('USE_DB_UPSERT'):
        query = """
            INSERT INTO document_view (document_id, field_data, user_id)
            VALUES (%(document_id)s,  %(field_data)s, %(user_id)s)
            ON CONFLICT (document_id, user_id) DO UPDATE SET field_data = %(field_data)s;
        """
        with database.cursor() as cursor:
            cursor.execute(query, args)
        database.commit()
    else:
        try:
            query = """
                INSERT INTO document_view (document_id, field_data, user_id)
                VALUES(%(document_id)s,  %(field_data)s, %(user_id)s)
            """
            with database.cursor() as cursor:
                cursor.execute(query, args)

        except:
            database.rollback()
            query = """
                UPDATE document_view SET field_data = %(field_data)s where document_id= %(document_id)s and user_id = %(user_id)s;
            """
            with database.cursor() as cursor:
                cursor.execute(query, args)
        database.commit()
    return


def document_set_status(document_set_id):
    database = get_db()
    query = """
        SELECT document_set_status(%(document_set_id)s)
    """

    with database.cursor() as cursor:
        cursor.execute(query, {
            'document_set_id': document_set_id
        })
        data = cursor.fetchone()
        return data

def get_signature_requests(user_id):
    """
    Get outstanding signature requests
    """
    database = get_db()
    query = """
        SELECT signature_requests(%(user_id)s)
    """

    with database.cursor() as cursor:
        cursor.execute(query, {
            'user_id': user_id
        })
        data = cursor.fetchone()
        return data[0] or []


def get_contacts(user_id):
    """
    Get a user's contacts.

    For now, this is just a list of people they have sent signature request before.
    """

    database = get_db()
    query = """
        SELECT DISTINCT users.user_id, users.name, users.email
        FROM document_sets
        JOIN documents ON document_sets.document_set_id = documents.document_set_id
        JOIN sign_requests ON documents.document_id = sign_requests.document_id
        JOIN users ON sign_requests.user_id = users.user_id
        WHERE document_sets.user_id = %(user_id)s
    """

    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, {'user_id': user_id})
        data = cursor.fetchall()
        return [dict(x) for x in data]


def get_sign_request(user_id, sign_request_id):
    database = get_db()
    query = """
        SELECT sign_request_id
        FROM sign_requests
        WHERE user_id = %(user_id)s AND sign_request_id = %(sign_request_id)s
    """

    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, {'user_id': user_id, 'sign_request_id': sign_request_id})
        result = cursor.fetchone()
        database.commit()
        return result


def get_latest_version(document_id):
    database = get_db()
    query = """
        SELECT latest_document_id(%(document_id)s)
    """
    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, {'document_id': document_id})
        result = cursor.fetchone()['latest_document_id']
        database.commit()
        return result


def get_document_set_owner(set_id):
    """
    Get the owner of a document set
    """
    database = get_db()
    query = """
        SELECT users.*
        FROM document_sets
        JOIN users ON document_sets.user_id = users.user_id
        WHERE document_sets.document_set_id = %(set_id)s
    """

    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, { 'set_id': set_id })
        data = cursor.fetchone()
        database.commit()
        return dict(data)


def get_document_status(doc_id):
    """
    Get the owner of a document set
    """
    database = get_db()
    query = """
        SELECT document_status(%(doc_id)s)
    """

    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, { 'doc_id': doc_id })
        data = cursor.fetchone()
        database.commit()
        return dict(data)

def get_document_set_recipients(set_id):
    """
    Get the recipients for a document set
    """

    database = get_db()
    query = """
        SELECT DISTINCT users.*
        FROM documents
        JOIN sign_requests ON documents.document_id = sign_requests.document_id
        JOIN users ON sign_requests.user_id = users.user_id
        WHERE documents.document_set_id = %(set_id)s
    """

    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, {'set_id': set_id})
        data = cursor.fetchall()
        database.commit()
        return [dict(x) for x in data]


def get_document_set_signers(set_id):
    """
    Get the recipients for a document set
    """
    database = get_db()
    query = """
        SELECT DISTINCT u.user_id, u.name, u.email, bool_or(accepted) as any_accepted
        FROM documents
        JOIN sign_requests sr ON documents.document_id = sr.document_id
        JOIN sign_results srr ON srr.sign_request_id = sr.sign_request_id
        JOIN users u ON sr.user_id = u.user_id
        WHERE documents.document_set_id = %(set_id)s
        GROUP BY u.user_id, u.name, u.email
    """

    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, {'set_id': set_id})
        data = cursor.fetchall()
        database.commit()
        return [dict(x) for x in data]


def get_usage(user_id, default_amount_per_unit, default_unit):
    database = get_db()
    query = """
        SELECT * from usage(%(user_id)s, %(default_amount_per_unit)s, %(default_unit)s)
    """

    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, { 'user_id': user_id,
                       'default_amount_per_unit': default_amount_per_unit,
                       'default_unit': default_unit})
        data = cursor.fetchone()
        database.commit()
        return dict(data)


def signed_by(user_id, file_hash):
    database = get_db()
    query = """
        SELECT signed_by(%(hash)s)
    """

    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, { 'user_id': user_id,
                       'hash': file_hash})
        data = cursor.fetchone()
        database.commit()
        return data['signed_by']


def get_user_meta(user_id):
    database = get_db()
    query = """
        SELECT data
        FROM user_meta
        WHERE user_id = %(user_id)s
    """

    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, { 'user_id': user_id })
        try:
            return cursor.fetchone().get('data')
        except:
            return {}
        finally:
            database.commit()



def update_user_meta(user_id, meta):
    database = get_db()

    if current_app.config.get('USE_DB_UPSERT'):
        query = """
            INSERT INTO user_meta
                (user_id, data)
            VALUES
                (%(user_id)s, %(data)s)

            ON CONFLICT (user_id)
                DO UPDATE SET data = %(data)s;
        """

        with database.cursor() as cursor:
            cursor.execute(query, {
                'user_id': user_id,
                'data': meta
            })
    else:
        try:
            query = """
                INSERT INTO user_meta (user_id, data)
                VALUES (%(user_id)s, %(data)s)
            """

            with database.cursor() as cursor:
                cursor.execute(query, {
                    'user_id': user_id,
                    'data': meta
                })

        except:
            database.rollback()

            query = """
                UPDATE user_meta SET data = %(data)s where user_id = %(user_id)s
            """

            with database.cursor() as cursor:
                cursor.execute(query, {
                    'user_id': user_id,
                    'data': meta
                })

    database.commit()


def user_owns_document(user_id, document_id):
    database = get_db()
    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        query = """
            SELECT ds.document_set_id  as document_set_id
            FROM documents d
            JOIN document_sets ds on ds.document_set_id = d.document_set_id
            WHERE ds.user_id = %(user_id)s and document_id = %(document_id)s
        """
        cursor.execute(query, {
                       'user_id': user_id,
                       'document_id': document_id
                       })

        result = cursor.fetchone()
        database.commit()
        return True if result else False


def order_documents(user_id, document_set_id, document_ids):
    database = get_db()
    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        for index, document_id in enumerate(document_ids):
            query = """
                UPDATE documents d SET order_index = %(order_index)s
                FROM document_sets ds
                WHERE d.document_set_id = ds.document_set_id and ds.user_id = %(user_id)s and d.document_id = %(document_id)s
            """
            cursor.execute(query, {
                           'user_id': user_id,
                           'document_id': document_id,
                           'document_set_id': document_set_id,
                           'order_index': index
                           })
    database.commit()


def add_merged_file(data, document_ids):
    database = get_db()
    query = """
        SELECT add_merged_file(%(data)s, %(document_ids)s::uuid[])
    """
    with database.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, { 'data': psycopg2.Binary(data), 'document_ids': document_ids})
        database.commit()
