import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material

Pane {
    objectName: 'About'

    property string title: qsTr("About Electrum")

    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: rootLayout.height
        interactive: height < contentHeight

        GridLayout {
            id: rootLayout
            columns: 2
            width: parent.width

            Image {
                id: electrum_logo
                Layout.columnSpan: 2
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: parent.width
                Layout.topMargin: constants.paddingXLarge
                Layout.bottomMargin: constants.paddingXLarge
                Layout.preferredHeight: width * implicitHeight / implicitWidth
                fillMode: Image.PreserveAspectFit
                source: '../../icons/electrum_banner_dark.png'
            }

            Label {
                text: qsTr('Version')
                Layout.alignment: Qt.AlignRight
            }
            Label {
                text: BUILD.electrum_version
            }
            Label {
                text: qsTr('Protocol version')
                Layout.alignment: Qt.AlignRight
            }
            Label {
                text: BUILD.protocol_version
            }
            Label {
                text: qsTr('Qt Version')
                Layout.alignment: Qt.AlignRight
            }
            Label {
                text: BUILD.qt_version
            }
            Label {
                text: qsTr('PyQt Version')
                Layout.alignment: Qt.AlignRight
            }
            Label {
                text: BUILD.pyqt_version
            }
            Label {
                text: qsTr('License')
                Layout.alignment: Qt.AlignRight
            }
            Label {
                text: qsTr('MIT License')
            }
            Label {
                text: qsTr('Homepage')
                Layout.alignment: Qt.AlignRight
            }
            Label {
                Layout.fillWidth: true
                text: '<a href="https://github.com/DebitMyData-PoW/electrum">https://github.com/DebitMyData-PoW/electrum</a>'
                textFormat: Text.RichText
                wrapMode: Text.WrapAnywhere
                onLinkActivated: Qt.openUrlExternally(link)
            }
            Label {
                text: qsTr('Developers')
                Layout.alignment: Qt.AlignRight
            }
            Label {
                text: 'Thomas Voegtlin\nSomberNight\nSander van Grieken\nFelix B.'
            }
            Item {
                width: 1
                height: constants.paddingXLarge
                Layout.columnSpan: 2
            }
            Label {
                text: qsTr('DebitMyData-Electrum, based on Electrum by Electrum Technologies GmbH')
                Layout.columnSpan: 2
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
            }
        }
    }

}
