export function embedFile(fileURL) {
    return (
        <embed
            src={fileURL}
            style={{ height: '100%', width: '100%' }}
        >
        </embed>)
}

export function getFileNameAndUrl(e) {
    let fileName = e.target.value.split("\\").pop();
    let fileURL = URL.createObjectURL(e.target.files[0]);
    if (fileName.endsWith('.pdf')) {
        return [fileName, fileURL];
    }
}

export async function findTerms(fileURL, fileType) {
    let contentType;
    let body;
    let paragraphs;
    // Sets up server request.
    if (fileType == 'HTML') {
        paragraphs = Array.from(document.getElementsByTagName("p"));
        let parasInner = [];
        paragraphs.forEach(function (item) {
            parasInner.push(item.innerHTML);
        });
        body = parasInner;
        contentType = 'application/json';
    }
    else if (fileType == 'PDF') {
        let objectURL = await fetch(fileURL);
        let blob = await objectURL.blob();
        body = blob;
        contentType = 'application/pdf'
    }
    // Sends paragraph text, or PDF blob to server.
    let resultsObj = await serverRequest(fileType, 'POST', body, contentType);
    resultsObj['termResults'].forEach(result => {
        result.key = result.term;
    })

    // For web pages, highlights terms on page.
    if (fileType == 'HTML') {
        let pattern = [];
        resultsObj['termResults'].forEach((result) => {
            pattern.push(result.term);
        })
        pattern = pattern.join('|');
        let styleString = '<span style="font-weight:bold; background-color:orange; color:black">';
        // Excludes already highlighted matches and subsets; excludes html; 
        // matches whole term only.
        pattern = '(?<!' + styleString + '[^<]*)' + '(?<!<[^>]*)' + '\\b(' + pattern + ')\\b';
        paragraphs.forEach((paragraph) => {
            // g to match all instances, i for case-insensitive.
            let re = new RegExp(pattern, "gi");
            let text = paragraph.innerHTML;
            let newText = text.replace(re, styleString + `$&</span>`);
            paragraph.innerHTML = newText;
        });
        return resultsObj['termResults']
    }
    // For PDFs, displays tagged PDF in tab.
    else {
        // Converts base64 response to PDF object URL and embeds it into 
        // <embed>. 
        let binary = atob(resultsObj['encodedPDF'].replace(/\s/g, ''));
        let len = binary.length;
        let buffer = new ArrayBuffer(len);
        let view = new Uint8Array(buffer);
        for (let i = 0; i < len; i++) {
            view[i] = binary.charCodeAt(i);
        }
        let blob = new Blob([view], { type: "application/pdf" });
        let objectURL = URL.createObjectURL(blob);
        return [objectURL, resultsObj['termResults']];
    }
}


export async function serverRequest(type, method, body, contentType) {
    if (!contentType) {
        contentType = 'application/json'
    }
    if (body && contentType == 'application/json') {
        body = JSON.stringify(body)
    }
    let response = await fetch(
        'http://127.0.0.1:5000/home', {
        headers: { 'Content-Type': contentType, 'type': type },
        method: method,
        body: body
    });
    let responseObj = JSON.parse(await response.text());
    return responseObj
}

export function formatExtractedText(text, lineBreaks) {
    let replacePattern = new RegExp(`(\n{1,})|(\r{1,})`, "g");
    let segments = text.split(replacePattern);
    return segments.map(
        (segment, index) => {
            if (replacePattern.test(segment)) {
                if (lineBreaks) {
                    return <span key={index}> <br /><br /></span>;
                }
                else {
                    return <span className="line-sep-icon" key={index}>&#9724;</span>
                }
            }
            else {
                return segment
            }
        })
}


export function formatTextAndHighlightMatches(termResults, text) {
    let terms = [];
    termResults.forEach(result => {
        terms.push(result['term']);

    })
    let lineBreakPattern = new RegExp(`(\n{1,})|(\r{1,})`, "g");
    let termsPattern;
    let segments;
    if (terms.length) {
        terms = terms.join('|');
        termsPattern = new RegExp(`\\b(${terms})\\b|(\n{1,})|(\r{1,})`, "gi");
        segments = text.split(termsPattern);
        return <>
            {
                segments.map(
                    (segment, index) => {
                        if (lineBreakPattern.test(segment)) {
                            return <span key={index}> <br /><br /></span>;
                        }
                        else if (termsPattern.test(segment)) {
                            return <span key={index} className='highlight'>{segment}</span >;
                        }
                        else if (segment) {
                            return <span key={index}>{segment}</span>;
                        }
                    }
                )
            }
        </>

    }
    else {
        segments = text.split(lineBreakPattern);
        return segments.map(
            (segment, index) => {
                if (lineBreakPattern.test(segment)) {
                    return <span key={index}> <br /><br /></span>;
                }
                else {
                    return segment
                }
            })
    }
}



// TESTING
export const dummyResults = [
    {
        "repos": [
            {
                "author": {
                    "bio": "SecureAuth is an identity security company that enables the most secure and flexible authentication experience for employees, partners and customers.",
                    "blogURL": "https://www.secureauth.com",
                    "name": "SecureAuthCorp",
                    "twitter": null,
                    "url": "https://github.com/SecureAuthCorp"
                },
                "description": "Impacket is a collection of Python classes for working with network protocols.",
                "name": "impacket",
                "url": "https://github.com/SecureAuthCorp/impacket"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "maaaaz",
                    "twitter": null,
                    "url": "https://github.com/maaaaz"
                },
                "description": "The great impacket example scripts compiled for Windows",
                "name": "impacket-examples-windows",
                "url": "https://github.com/maaaaz/impacket-examples-windows"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "ropnop",
                    "twitter": null,
                    "url": "https://github.com/ropnop"
                },
                "description": "Standalone binaries for Linux/Windows of Impacket's examples",
                "name": "impacket_static_binaries",
                "url": "https://github.com/ropnop/impacket_static_binaries"
            },
            {
                "author": {
                    "bio": "Val is a Solutions Architect with a passion for building performant software applications with optimal quality of experience",
                    "blogURL": "neekware.com",
                    "name": "un33k",
                    "twitter": "UneekVu",
                    "url": "https://github.com/un33k"
                },
                "description": "Automatically exported from code.google.com/p/impacket",
                "name": "impacket",
                "url": "https://github.com/un33k/impacket"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "kanzure",
                    "twitter": "kanzure",
                    "url": "https://github.com/kanzure"
                },
                "description": "pure-python reverse engineering of DCE/RPC and SMB",
                "name": "impacket",
                "url": "https://github.com/kanzure/impacket"
            }
        ],
        "term": "Impacket",
        "key": "Impacket"
    },
    {
        "repos": [
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "hzqst",
                    "twitter": null,
                    "url": "https://github.com/hzqst"
                },
                "description": "Vmware Hardened VM detection mitigation loader (anti anti-vm)",
                "name": "VmwareHardenedLoader",
                "url": "https://github.com/hzqst/VmwareHardenedLoader"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "gentoo",
                    "twitter": null,
                    "url": "https://github.com/gentoo"
                },
                "description": "[MIRROR] VMware desktop ebuilds",
                "name": "vmware",
                "url": "https://github.com/gentoo/vmware"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "https://vmware.com",
                    "name": "vmware",
                    "twitter": "vmwopensource",
                    "url": "https://github.com/vmware"
                },
                "description": "Clarity is a scalable, accessible, customizable, open source design system built with web components. Works with any JavaScript framework, built for enterprises, and designed to  be inclusive.",
                "name": "clarity",
                "url": "https://github.com/vmware/clarity"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "malichite",
                    "twitter": null,
                    "url": "https://github.com/malichite"
                },
                "description": null,
                "name": "VMWare",
                "url": "https://github.com/malichite/VMWare"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "https://www.williamlam.com/",
                    "name": "lamw",
                    "twitter": "lamw",
                    "url": "https://github.com/lamw"
                },
                "description": "Various scripts for VMware based solutions",
                "name": "vmware-scripts",
                "url": "https://github.com/lamw/vmware-scripts"
            }
        ],
        "term": "VMware",
        "key": "VMware"
    },
    {
        "repos": [
            {
                "author": {
                    "bio": null,
                    "blogURL": "binarly.io",
                    "name": "REhints",
                    "twitter": "rehints",
                    "url": "https://github.com/REhints"
                },
                "description": null,
                "name": "WinDbg",
                "url": "https://github.com/REhints/WinDbg"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "pccq2002",
                    "twitter": null,
                    "url": "https://github.com/pccq2002"
                },
                "description": "windbg open source",
                "name": "windbg",
                "url": "https://github.com/pccq2002/windbg"
            },
            {
                "author": {
                    "bio": "Corelan Consulting",
                    "blogURL": "https://www.corelan-consulting.com",
                    "name": "corelan",
                    "twitter": "corelanconsult",
                    "url": "https://github.com/corelan"
                },
                "description": "Public repository for windbglib, a wrapper around pykd.pyd (for Windbg), used by mona.py",
                "name": "windbglib",
                "url": "https://github.com/corelan/windbglib"
            },
            {
                "author": {
                    "bio": "Yet another @blahcat  (Discord: hugsy#0766)",
                    "blogURL": "https://blahcat.github.io",
                    "name": "hugsy",
                    "twitter": "_hugsy_",
                    "url": "https://github.com/hugsy"
                },
                "description": "DEFCON 27 workshop - Modern Debugging with WinDbg Preview",
                "name": "defcon_27_windbg_workshop",
                "url": "https://github.com/hugsy/defcon_27_windbg_workshop"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "bannedit",
                    "twitter": null,
                    "url": "https://github.com/bannedit"
                },
                "description": null,
                "name": "windbg",
                "url": "https://github.com/bannedit/windbg"
            }
        ],
        "term": "WinDbg",
        "key": "WinDbg"
    },
    {
        "repos": [
            {
                "author": {
                    "bio": "The Wireshark Network Protocol Analyzer",
                    "blogURL": "https://www.wireshark.org/",
                    "name": "wireshark",
                    "twitter": null,
                    "url": "https://github.com/wireshark"
                },
                "description": "Read-only mirror of Wireshark's Git repository at https://gitlab.com/wireshark/wireshark. GitHub won't let us disable pull requests. ☞ THEY WILL BE IGNORED HERE ☜ Please upload them at GitLab.",
                "name": "wireshark",
                "url": "https://github.com/wireshark/wireshark"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "http://www.bmc.com",
                    "name": "boundary",
                    "twitter": null,
                    "url": "https://github.com/boundary"
                },
                "description": "wireshark + boundary IPFIX decode patches",
                "name": "wireshark",
                "url": "https://github.com/boundary/wireshark"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "http://www.freerdp.com",
                    "name": "FreeRDP",
                    "twitter": null,
                    "url": "https://github.com/FreeRDP"
                },
                "description": "FreeRDP Wireshark RDP Protocol Analyzer",
                "name": "Wireshark",
                "url": "https://github.com/FreeRDP/Wireshark"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "themikewylie",
                    "twitter": null,
                    "url": "https://github.com/themikewylie"
                },
                "description": null,
                "name": "wireshark",
                "url": "https://github.com/themikewylie/wireshark"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "hongch911",
                    "twitter": null,
                    "url": "https://github.com/hongch911"
                },
                "description": "The H265 H264 PS PCM AMR SILK plugin for Wireshark Lua",
                "name": "WiresharkPlugin",
                "url": "https://github.com/hongch911/WiresharkPlugin"
            }
        ],
        "term": "Wireshark",
        "key": "Wireshark"
    },
    {
        "repos": [
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "deathmemory",
                    "twitter": null,
                    "url": "https://github.com/deathmemory"
                },
                "description": "利用 frida 获取 Jni RegisterNatives 动态注册的函数",
                "name": "fridaRegstNtv",
                "url": "https://github.com/deathmemory/fridaRegstNtv"
            },
            {
                "author": {
                    "bio": "https://denghao.me",
                    "blogURL": "",
                    "name": "denghao123",
                    "twitter": null,
                    "url": "https://github.com/denghao123"
                },
                "description": "javascript正则表达式集合",
                "name": "Regs",
                "url": "https://github.com/denghao123/Regs"
            },
            {
                "author": {
                    "bio": "Cyber Threat Management and Security Analytics",
                    "blogURL": "www.encodegroup.com",
                    "name": "EncodeGroup",
                    "twitter": null,
                    "url": "https://github.com/EncodeGroup"
                },
                "description": "Dumping SAM / SECURITY / SYSTEM registry hives with a Beacon Object File",
                "name": "BOF-RegSave",
                "url": "https://github.com/EncodeGroup/BOF-RegSave"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "Seabreg",
                    "twitter": null,
                    "url": "https://github.com/Seabreg"
                },
                "description": "Regshot is a small, free and open-source registry compare utility that allows you to quickly take a snapshot of your registry and then compare it with a second one - done after doing system changes or installing a new software product",
                "name": "Regshot",
                "url": "https://github.com/Seabreg/Regshot"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "Dankirk",
                    "twitter": null,
                    "url": "https://github.com/Dankirk"
                },
                "description": "A tool for scanning registery key permissions. Find where non-admins can create symbolic links.",
                "name": "RegSLScan",
                "url": "https://github.com/Dankirk/RegSLScan"
            }
        ],
        "term": "regs",
        "key": "regs"
    },
    {
        "repos": [
            {
                "author": {
                    "bio": "SecureAuth is an identity security company that enables the most secure and flexible authentication experience for employees, partners and customers.",
                    "blogURL": "https://www.secureauth.com",
                    "name": "SecureAuthCorp",
                    "twitter": null,
                    "url": "https://github.com/SecureAuthCorp"
                },
                "description": "Impacket is a collection of Python classes for working with network protocols.",
                "name": "impacket",
                "url": "https://github.com/SecureAuthCorp/impacket"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "maaaaz",
                    "twitter": null,
                    "url": "https://github.com/maaaaz"
                },
                "description": "The great impacket example scripts compiled for Windows",
                "name": "impacket-examples-windows",
                "url": "https://github.com/maaaaz/impacket-examples-windows"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "ropnop",
                    "twitter": null,
                    "url": "https://github.com/ropnop"
                },
                "description": "Standalone binaries for Linux/Windows of Impacket's examples",
                "name": "impacket_static_binaries",
                "url": "https://github.com/ropnop/impacket_static_binaries"
            },
            {
                "author": {
                    "bio": "Val is a Solutions Architect with a passion for building performant software applications with optimal quality of experience",
                    "blogURL": "neekware.com",
                    "name": "un33k",
                    "twitter": "UneekVu",
                    "url": "https://github.com/un33k"
                },
                "description": "Automatically exported from code.google.com/p/impacket",
                "name": "impacket",
                "url": "https://github.com/un33k/impacket"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "kanzure",
                    "twitter": "kanzure",
                    "url": "https://github.com/kanzure"
                },
                "description": "pure-python reverse engineering of DCE/RPC and SMB",
                "name": "impacket",
                "url": "https://github.com/kanzure/impacket"
            }
        ],
        "term": "impacket",
        "key": "impacket"
    },
    {
        "repos": [
            {
                "author": {
                    "bio": "Production Engineer @Shopify",
                    "blogURL": "",
                    "name": "jlaffaye",
                    "twitter": "jlaffaye",
                    "url": "https://github.com/jlaffaye"
                },
                "description": "FTP client package for Go",
                "name": "ftp",
                "url": "https://github.com/jlaffaye/ftp"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "https://www.haugas.com",
                    "name": "Siim",
                    "twitter": null,
                    "url": "https://github.com/Siim"
                },
                "description": "Lightweight FTP server written in C",
                "name": "ftp",
                "url": "https://github.com/Siim/ftp"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "xlxl2010",
                    "twitter": null,
                    "url": "https://github.com/xlxl2010"
                },
                "description": "java断点上传下载FTP服务器文件的例子，进度条显示",
                "name": "FTP",
                "url": "https://github.com/xlxl2010/FTP"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "https://www.linkedin.com/in/rebeccasagalyn",
                    "name": "beckysag",
                    "twitter": null,
                    "url": "https://github.com/beckysag"
                },
                "description": "Simple FTP client-server implementation in C",
                "name": "ftp",
                "url": "https://github.com/beckysag/ftp"
            },
            {
                "author": {
                    "bio": "Engineer@Tencent",
                    "blogURL": "http://chenxiaoyu.org",
                    "name": "smallfish",
                    "twitter": null,
                    "url": "https://github.com/smallfish"
                },
                "description": "FTP Client For Go(lang)",
                "name": "ftp",
                "url": "https://github.com/smallfish/ftp"
            }
        ],
        "term": "FTP",
        "key": "FTP"
    },
    {
        "repos": [
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "go-cmd",
                    "twitter": null,
                    "url": "https://github.com/go-cmd"
                },
                "description": "Non-blocking external commands in Go with and streaming output and concurrent-safe access",
                "name": "cmd",
                "url": "https://github.com/go-cmd/cmd"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "http://xorm.io",
                    "name": "go-xorm",
                    "twitter": null,
                    "url": "https://github.com/go-xorm"
                },
                "description": "Command line tools for database operation written by Go, moved to https://gitea.com/xorm/cmd",
                "name": "cmd",
                "url": "https://github.com/go-xorm/cmd"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "revel.github.io",
                    "name": "revel",
                    "twitter": null,
                    "url": "https://github.com/revel"
                },
                "description": "Command line tools for Revel.",
                "name": "cmd",
                "url": "https://github.com/revel/cmd"
            },
            {
                "author": {
                    "bio": "Principal Engineer @avalara. Previously @indix @thoughtworks. #kubernetes #terraform #docker #scala #javascript #nodejs. Author of http://bit.ly/learningci ",
                    "blogURL": "http://stacktoheap.com",
                    "name": "manojlds",
                    "twitter": null,
                    "url": "https://github.com/manojlds"
                },
                "description": "C# library to run external programs in a simpler way. Demonstration of \"dynamic\" features of C#.",
                "name": "cmd",
                "url": "https://github.com/manojlds/cmd"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "cmderdev",
                    "twitter": null,
                    "url": "https://github.com/cmderdev"
                },
                "description": "Lovely console emulator package for Windows",
                "name": "cmder",
                "url": "https://github.com/cmderdev/cmder"
            }
        ],
        "term": "cmd",
        "key": "cmd"
    },
    {
        "repos": [
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "OpenWireSec",
                    "twitter": null,
                    "url": "https://github.com/OpenWireSec"
                },
                "description": null,
                "name": "metasploit",
                "url": "https://github.com/OpenWireSec/metasploit"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "http://www.rapid7.com/",
                    "name": "rapid7",
                    "twitter": null,
                    "url": "https://github.com/rapid7"
                },
                "description": "Metasploit Framework",
                "name": "metasploit-framework",
                "url": "https://github.com/rapid7/metasploit-framework"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "http://www.rapid7.com/",
                    "name": "rapid7",
                    "twitter": null,
                    "url": "https://github.com/rapid7"
                },
                "description": "Metasploitable3 is a VM that is built from the ground up with a large amount of security vulnerabilities.",
                "name": "metasploitable3",
                "url": "https://github.com/rapid7/metasploitable3"
            },
            {
                "author": {
                    "bio": "Security engineer for and cofounder of HardenedBSD.",
                    "blogURL": "https://hardenedbsd.org/",
                    "name": "lattera",
                    "twitter": null,
                    "url": "https://github.com/lattera"
                },
                "description": null,
                "name": "metasploit",
                "url": "https://github.com/lattera/metasploit"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "https://staaldraad.github.io",
                    "name": "staaldraad",
                    "twitter": "_staaldraad",
                    "url": "https://github.com/staaldraad"
                },
                "description": "Metasploit things, modules, plugins, exploits",
                "name": "metasploit",
                "url": "https://github.com/staaldraad/metasploit"
            }
        ],
        "term": "Metasploit",
        "key": "Metasploit"
    },
    {
        "repos": [
            {
                "author": {
                    "bio": "Security Engineer",
                    "blogURL": "",
                    "name": "kbandla",
                    "twitter": "kbandla",
                    "url": "https://github.com/kbandla"
                },
                "description": "ImmunityDebugger",
                "name": "ImmunityDebugger",
                "url": "https://github.com/kbandla/ImmunityDebugger"
            },
            {
                "author": {
                    "bio": "Security Engineer",
                    "blogURL": "",
                    "name": "kbandla",
                    "twitter": "kbandla",
                    "url": "https://github.com/kbandla"
                },
                "description": "PyCommands for Immunity Debugger",
                "name": "ImmunityDebuggerScripts",
                "url": "https://github.com/kbandla/ImmunityDebuggerScripts"
            },
            {
                "author": {
                    "bio": "Cyber Security Researcher",
                    "blogURL": "https://twitter.com/R0m4nZ41k1n",
                    "name": "romanzaikin",
                    "twitter": null,
                    "url": "https://github.com/romanzaikin"
                },
                "description": "Make OllyDbg v1.10 Look like Immunity Debugger & Best Plugins",
                "name": "OllyDbg-v1.10-With-Best-Plugins-And-Immunity-Debugger-theme-",
                "url": "https://github.com/romanzaikin/OllyDbg-v1.10-With-Best-Plugins-And-Immunity-Debugger-theme-"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "notzen",
                    "twitter": null,
                    "url": "https://github.com/notzen"
                },
                "description": "Immunity Debugger Repository",
                "name": "ImmunityDebugger",
                "url": "https://github.com/notzen/ImmunityDebugger"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "jon1scr",
                    "twitter": null,
                    "url": "https://github.com/jon1scr"
                },
                "description": "ImmunityDebugger",
                "name": "ImmunityDebugger",
                "url": "https://github.com/jon1scr/ImmunityDebugger"
            }
        ],
        "term": "Immunity Debugger",
        "key": "Immunity Debugger"
    },
    {
        "repos": [
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "mefistotelis",
                    "twitter": null,
                    "url": "https://github.com/mefistotelis"
                },
                "description": "Plugin for IDA Pro disassembler which allows loading .map files.",
                "name": "ida-pro-loadmap",
                "url": "https://github.com/mefistotelis/ida-pro-loadmap"
            },
            {
                "author": {
                    "bio": "We are a Software Development Company with a highly skilled team of engineers specialized in Microsoft technologies",
                    "blogURL": "http://www.nektra.com",
                    "name": "nektra",
                    "twitter": null,
                    "url": "https://github.com/nektra"
                },
                "description": "Identifying Virtual Table Functions using VTBL IDA Pro Plugin + Deviare Hooking Engine",
                "name": "vtbl-ida-pro-plugin",
                "url": "https://github.com/nektra/vtbl-ida-pro-plugin"
            },
            {
                "author": {
                    "bio": "Fanatic python programmer.\r\nBelieves in open source projects.",
                    "blogURL": "www.techbliss.org",
                    "name": "techbliss",
                    "twitter": "zadow28",
                    "url": "https://github.com/techbliss"
                },
                "description": "Frida PluginFor Ida Pro",
                "name": "Frida_For_Ida_Pro",
                "url": "https://github.com/techbliss/Frida_For_Ida_Pro"
            },
            {
                "author": {
                    "bio": "OJBK",
                    "blogURL": "https://89tool.com",
                    "name": "kuustudio",
                    "twitter": null,
                    "url": "https://github.com/kuustudio"
                },
                "description": "IDA_Pro_7.2",
                "name": "IDA_Pro_7.2",
                "url": "https://github.com/kuustudio/IDA_Pro_7.2"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "yutewiyof",
                    "twitter": null,
                    "url": "https://github.com/yutewiyof"
                },
                "description": "Введение в реверсинг с нуля, используя IDA PRO. Перевод от Яши",
                "name": "intro-rev-ida-pro",
                "url": "https://github.com/yutewiyof/intro-rev-ida-pro"
            }
        ],
        "term": "IDA Pro",
        "key": "IDA Pro"
    },
    {
        "repos": [
            {
                "author": {
                    "bio": "An open-source x64/x32 debugger for windows.",
                    "blogURL": "http://x64dbg.com",
                    "name": "x64dbg",
                    "twitter": null,
                    "url": "https://github.com/x64dbg"
                },
                "description": "Implementation of OllyDbg 1.10 plugin SDK for x64dbg.",
                "name": "OllyDbg",
                "url": "https://github.com/x64dbg/OllyDbg"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "https://doar-e.github.io/",
                    "name": "0vercl0k",
                    "twitter": "0vercl0k",
                    "url": "https://github.com/0vercl0k"
                },
                "description": "Scripting OllyDBG2 using Python is now possible!",
                "name": "ollydbg2-python",
                "url": "https://github.com/0vercl0k/ollydbg2-python"
            },
            {
                "author": {
                    "bio": "Computer Security Researcher............ \r\n菜刀切肉，亦能过狗。\r\ndubuqingfeng.eth",
                    "blogURL": "https://dubuqingfeng.xyz",
                    "name": "dubuqingfeng",
                    "twitter": "dubuqingfeng",
                    "url": "https://github.com/dubuqingfeng"
                },
                "description": "some ollydbg scripts.",
                "name": "ollydbg-script",
                "url": "https://github.com/dubuqingfeng/ollydbg-script"
            },
            {
                "author": {
                    "bio": "Software engineer with interests in mathematics and graph technologies.",
                    "blogURL": "",
                    "name": "ThomasThelen",
                    "twitter": null,
                    "url": "https://github.com/ThomasThelen"
                },
                "description": "Unpacking scripts for Ollydbg.",
                "name": "OllyDbg-Scripts",
                "url": "https://github.com/ThomasThelen/OllyDbg-Scripts"
            },
            {
                "author": {
                    "bio": "APT Hunter, Threat Hunter, Incident Responder, Forensics Analyst, Information Security Consultant, Red Teamer (Network+System views)",
                    "blogURL": "https://trietptm.com",
                    "name": "trietptm",
                    "twitter": null,
                    "url": "https://github.com/trietptm"
                },
                "description": "All the latest releases and files for OllyDbg...",
                "name": "OllyDbg-Archive",
                "url": "https://github.com/trietptm/OllyDbg-Archive"
            }
        ],
        "term": "OllyDbg",
        "key": "OllyDbg"
    },
    {
        "repos": [
            {
                "author": {
                    "bio": "I turn cuca into software & science.",
                    "blogURL": "http://blog.thiagopradi.net/",
                    "name": "thiagopradi",
                    "twitter": null,
                    "url": "https://github.com/thiagopradi"
                },
                "description": "Database Sharding for ActiveRecord",
                "name": "octopus",
                "url": "https://github.com/thiagopradi/octopus"
            },
            {
                "author": {
                    "bio": "I write codes that break codes, Hacker wannabe.\r\n",
                    "blogURL": "https://shells.systems",
                    "name": "mhaskar",
                    "twitter": "mohammadaskar2",
                    "url": "https://github.com/mhaskar"
                },
                "description": "Open source pre-operation C2 server based on python and powershell",
                "name": "Octopus",
                "url": "https://github.com/mhaskar/Octopus"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "https://scholar.google.de/citations?user=tJlD24EAAAAJ",
                    "name": "thmoa",
                    "twitter": null,
                    "url": "https://github.com/thmoa"
                },
                "description": "This repository contains code corresponding to the paper Learning to Reconstruct People in Clothing from a Single RGB Camera.",
                "name": "octopus",
                "url": "https://github.com/thmoa/octopus"
            },
            {
                "author": {
                    "bio": "Advanced Fuzzing Online Trainings and Security Research Services",
                    "blogURL": "https://fuzzinglabs.com/",
                    "name": "FuzzingLabs",
                    "twitter": "FuzzingLabs",
                    "url": "https://github.com/FuzzingLabs"
                },
                "description": "Security Analysis tool for WebAssembly module (wasm) and Blockchain Smart Contracts (BTC/ETH/NEO/EOS)",
                "name": "octopus",
                "url": "https://github.com/FuzzingLabs/octopus"
            },
            {
                "author": {
                    "bio": null,
                    "blogURL": "",
                    "name": "zjcscut",
                    "twitter": null,
                    "url": "https://github.com/zjcscut"
                },
                "description": "长链接压缩为短链接的服务",
                "name": "octopus",
                "url": "https://github.com/zjcscut/octopus"
            }
        ],
        "term": "octopus",
        "key": "octopus"
    }
];

export const dummyAuthorWatchlist = [...Array(30)].map((_, i) => (
    { name: `author${i}`, twitter: `author${i}`, url: `www.url${i}.com` }))

