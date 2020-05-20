#![allow(dead_code)]

use std::collections::HashMap;

pub struct Object<'a> {
    val: &'a str,
    slot: HashMap<&'a str, Object<'a>>,
    nest: Vec<Object<'a>>,
}

use std::fmt;

impl fmt::Display for Object<'_> {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.dump(0, String::new()))
    }
}

impl fmt::Debug for Object<'_> {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.dump(0, String::new()))
    }
}

trait Dump {
    fn dump(&self, depth: u8, prefix: String) -> String;
    fn head(&self, prefix: String) -> String;
    fn _type(&self) -> &'static str;
    fn _val(&self) -> String;
    fn pad(&self, depth: u8) -> String;
}

impl Dump for Object<'_> {
    fn dump(&self, depth: u8, prefix: String) -> String {
        // header
        let mut tree = format!("{}{}", self.pad(depth), self.head(prefix));
        // nest[]ed
        let mut idx = 0;
        for i in &self.nest {
            tree.push_str(&i.dump(depth + 1, format!("{} = ", idx)));
            idx += 1;
        }
        // recursive subtree
        tree
    }

    fn head(&self, prefix: String) -> String {
        format!("{}<{}:{}>", prefix, self._type(), self._val())
    }

    fn _type(&self) -> &'static str {
        "object"
    }

    fn _val(&self) -> String {
        format!("{}", self.val)
    }

    fn pad(&self, depth: u8) -> String {
        let mut padding = String::from("\n");
        for _i in 0..depth {
            padding += "\t";
        }
        padding
    }
}

impl<'a> Object<'a> {
    fn new(v: &str) -> Object {
        Object {
            val: v,
            slot: HashMap::new(),
            nest: Vec::new(),
        }
    }
}

trait Stack {
    fn push(&mut self, that: &Object);
}

impl Stack for Object<'_> {
    fn push(&mut self, that: &Object<'_>) {
        self.nest.push(that);
    }
}

lazy_static! {
    pub static ref VM: Object<'static> = Object::new("COVID");
}

pub fn init() {
    log::info!("init {:?}", Object::new("debug"));
    let mut x = Object::new("Hello");
    x.push(Object::new("World"));
    let vm = Object::new("COVID");
    x.push(vm);
    // x.push(x);
    log::info!("{:?}", x);
    log::info!("init {:?}", *VM);
}
