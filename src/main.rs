#[macro_use]
extern crate lazy_static;
mod graph;
mod metainfo;

fn main() {
    env_logger::init();
    log::info!("{}", metainfo::TITLE);
    log::info!("(c) {} 2002 {}", metainfo::AUTHOR, metainfo::LICENSE);
    graph::init();
}
