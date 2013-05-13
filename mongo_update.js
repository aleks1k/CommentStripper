/**
 * Created with PyCharm.
 * User: Alexey
 * Date: 10.05.13
 * Time: 0:09
 * To change this template use File | Settings | File Templates.
 */
db = connect("localhost:27020/openInclude");
var docs = db.modules2.find();
docs.forEach(function(doc) { db.modules3.insert(doc) });
db.modules.renameCollection('modules_old');
db.modules3.renameCollection('modules');
db.modules2.drop()
